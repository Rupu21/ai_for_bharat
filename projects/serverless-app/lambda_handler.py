import boto3
import json
import base64
import time
import uuid
import os
from io import BytesIO
from random import randint
from datetime import datetime
def get_cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Access-Control-Allow-Headers,Access-Control-Allow-Origin,Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
    }
def calculate_base64_size(base64_string):
    """Calculate the size of a base64 encoded string in bytes"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_data = base64_string.split(',')[1]
        else:
            base64_data = base64_string
        # Calculate size: (length * 3/4) - padding
        padding = base64_data.count('=')
        size = (len(base64_data) * 3 // 4) - padding
        return size
    except Exception:
        return 0
def calculate_output_images_size(images):
    """Calculate total size of output images in bytes"""
    total_size = 0
    if images:
        for image in images:
            total_size += calculate_base64_size(image)
    return total_size
def log_to_dynamodb(request_id, model_id, prompt, mode, image_size, mask_size, output_size, generation_time_ms, success=True, error_message=None):
    """Log request data to DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'ImageGenerationTable')
        table = dynamodb.Table(table_name)
        item = {
            'id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'model_id': model_id,
            'prompt': prompt[:1000],
            'mode': mode,
            'image_base64_size_bytes': image_size,
            'mask_base64_size_bytes': mask_size,
            'output_images_size_bytes': output_size,
            'generation_time_ms': generation_time_ms,
            'success': success
        }
        if error_message:
            item['error_message'] = error_message[:500]
        table.put_item(Item=item)
        return True
    except Exception as e:
        # Log error but don't fail the main request
        print(f"Failed to log to DynamoDB: {str(e)}")
        return False
def prepare_titan_request(prompt_content, painting_mode, mask_base64, image_base64):
    """Prepare request body for Titan model"""
    image_generation_config = {
        "taskType": painting_mode,
        "imageGenerationConfig": {
            "numberOfImages": 2,
            "quality": "premium",
            "height": 1024,
            "width": 1024,
            "cfgScale": 8.0,
            "seed": randint(0, 100000),
        },
    }
    params = {
        "image": image_base64,
        "text": prompt_content,
        "maskImage": mask_base64
    }
    if painting_mode == 'OUTPAINTING':
        params['outPaintingMode'] = 'DEFAULT'
        image_generation_config['outPaintingParams'] = params
    elif painting_mode == 'precise-outpaint':
        params['outPaintingMode'] = 'PRECISE'
        image_generation_config['outPaintingParams'] = params
    else:
        image_generation_config['inPaintingParams'] = params
    return json.dumps(image_generation_config)
def lambda_handler(event, context):
    # Generate unique request ID for tracking
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Debug: Log the incoming event
    print(f"Received event: {json.dumps(event)}")
    
    # Extract the request body
    try:
        # Check if body exists
        if 'body' not in event:
            print("ERROR: 'body' key not found in event")
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Missing body in request', 'event_keys': list(event.keys())})
            }
        
        # Check if body is already a dict (direct Lambda invocation) or string (API Gateway)
        if isinstance(event['body'], dict):
            body = event['body']
        elif isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            print(f"ERROR: Unexpected body type: {type(event['body'])}")
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': f'Invalid body type: {type(event["body"])}'})
            }
            
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON decode error: {str(e)}")
        print(f"Body content: {event.get('body', 'NO BODY')[:200]}")
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Invalid JSON in request body: {str(e)}'})
        }
    except Exception as e:
        print(f"ERROR: Unexpected error parsing body: {str(e)}")
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Error parsing request body: {str(e)}'})
        }
    # Get the required parameters
    try:
        print(f"Body keys: {list(body.keys())}")
        
        # Validate prompt structure
        if 'prompt' not in body:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Missing "prompt" field', 'received_keys': list(body.keys())})
            }
        
        prompt_content = body['prompt']['text']
        painting_mode = body['prompt']['mode']
        
        # Validate mask
        if 'mask' not in body:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Missing "mask" field'})
            }
        mask_base64 = body['mask'].split(",")[1] if "," in body['mask'] else body['mask']
        
        # Validate base_image
        if 'base_image' not in body:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Missing "base_image" field'})
            }
        image_base64 = body['base_image'].split(",")[1] if "," in body['base_image'] else body['base_image']
        
    except KeyError as e:
        print(f"ERROR: Missing key: {str(e)}")
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Missing required field: {str(e)}', 'body_structure': str(body.keys())})
        }
    except IndexError as e:
        print(f"ERROR: Index error (likely malformed base64): {str(e)}")
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Malformed base64 image data'})
        }
    except Exception as e:
        print(f"ERROR: Unexpected error extracting parameters: {str(e)}")
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Error extracting parameters: {str(e)}'})
        }
    # Get optional model parameter (defaults to titan)
    model = body.get('model', 'titan').lower()
    canvas_config = body.get('canvas_config', {})
    # Calculate input image sizes
    image_size = calculate_base64_size(body['base_image'])
    mask_size = calculate_base64_size(body['mask'])
    # Validate model parameter
    if model not in ['titan']:
        error_msg = f'Unsupported model: {model}. Supported models: titan'
        # Log failed request
        log_to_dynamodb(
            request_id=request_id,
            model_id='unknown',
            prompt=prompt_content,
            mode=painting_mode,
            image_size=image_size,
            mask_size=mask_size,
            output_size=0,
            generation_time_ms=int((time.time() - start_time) * 1000),
            success=False,
            error_message=error_msg
        )
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': error_msg})
        }
    # Prepare request body for Titan model
    try:
        request_body = prepare_titan_request(prompt_content, painting_mode, mask_base64, image_base64)
        model_id = "amazon.titan-image-generator-v2:0"
    except Exception as e:
        error_msg = f'Error preparing request for {model}: {str(e)}'
        # Log failed request
        log_to_dynamodb(
            request_id=request_id,
            model_id=model_id if 'model_id' in locals() else 'unknown',
            prompt=prompt_content,
            mode=painting_mode,
            image_size=image_size,
            mask_size=mask_size,
            output_size=0,
            generation_time_ms=int((time.time() - start_time) * 1000),
            success=False,
            error_message=error_msg
        )
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': error_msg})
        }
    # Send the data to the Bedrock client
    try:
        # Record time before Bedrock call
        bedrock_start_time = time.time()
        session = boto3.Session()
        bedrock = session.client(service_name='bedrock-runtime')
        response_bedrock = bedrock.invoke_model(
            body=request_body,
            modelId=model_id,
            contentType="application/json",
            accept="application/json"
        )
        # Calculate generation time
        generation_time_ms = int((time.time() - bedrock_start_time) * 1000)
        # Get the output from the response
        response_output = json.loads(response_bedrock.get('body').read())
        images = response_output.get('images')
        # Calculate output images size
        output_size = calculate_output_images_size(images)
        # Log successful request to DynamoDB
        log_to_dynamodb(
            request_id=request_id,
            model_id=model_id,
            prompt=prompt_content,
            mode=painting_mode,
            image_size=image_size,
            mask_size=mask_size,
            output_size=output_size,
            generation_time_ms=generation_time_ms,
            success=True
        )
        # Return the response with CORS headers
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'images': images,
                'model_used': model,  # Include which model was used in response
                'request_id': request_id,  # Include request ID for tracking
                'generation_time_ms': generation_time_ms  # Include timing info
            })
        }
    except Exception as e:
        error_message = str(e)
        generation_time_ms = int((time.time() - start_time) * 1000)
        # Log failed request to DynamoDB
        log_to_dynamodb(
            request_id=request_id,
            model_id=model_id,
            prompt=prompt_content,
            mode=painting_mode,
            image_size=image_size,
            mask_size=mask_size,
            output_size=0,
            generation_time_ms=generation_time_ms,
            success=False,
            error_message=error_message
        )
        # Return an error response
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'error': error_message,
                'model_attempted': model,
                'request_id': request_id
            })
        }