"""MCP Client for communicating with traffic and restaurant MCP servers."""

import asyncio
import json
import random
import subprocess
import sys
import time
from typing import Any, Optional
from datetime import datetime, timedelta
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dashboard.models.data_models import TrafficDataPoint, RestaurantDataPoint
from dashboard.utils.logger import log_mcp_call, log_info, log_error, log_warning


class MCPClient:
    """Simplified MCP client for server communication."""
    
    def __init__(self, server_configs: dict[str, dict[str, Any]]):
        """
        Initialize MCP client with server configurations.
        
        Args:
            server_configs: Dictionary mapping server names to their configurations
        """
        self.server_configs = server_configs
    
    async def call_tool_direct(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any]
    ) -> Any:
        """
        Call MCP tool directly by running server as subprocess.
        This avoids the async context manager issues.
        """
        start_time = time.time()
        log_info(f"MCP Client: Calling {server_name}.{tool_name} with args: {arguments}")
        
        config = self.server_configs.get(server_name)
        if not config:
            error_msg = f"No configuration found for server: {server_name}"
            log_error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Create a simple JSON-RPC request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # For now, let's use a simpler approach - direct server execution
            # This is a simplified version that calls the server functions directly
            if server_name == "traffic-data":
                from mcp_servers.traffic_server import parse_coordinates, fetch_live_traffic_data
                
                zone_id = arguments.get("zone_id", "zone_1")
                lat, lon = parse_coordinates(zone_id)
                
                # Calculate dynamic count based on time and location
                current_hour = datetime.now().hour
                
                # Base traffic count varies by time of day
                if 7 <= current_hour <= 9 or 17 <= current_hour <= 19:  # Rush hours
                    base_traffic_count = random.randint(25, 45)
                elif 10 <= current_hour <= 16:  # Daytime
                    base_traffic_count = random.randint(15, 30)
                elif 22 <= current_hour or current_hour <= 6:  # Night
                    base_traffic_count = random.randint(5, 15)
                else:  # Evening
                    base_traffic_count = random.randint(12, 25)
                
                # Add location-based variation (busy areas have more traffic)
                # Major cities/busy coordinates get more traffic
                location_name = "Unknown"
                if abs(lat - 40.7589) < 0.1 and abs(lon + 73.9851) < 0.1:  # NYC area
                    base_traffic_count = int(base_traffic_count * 1.5)
                    location_name = "NYC"
                elif abs(lat - 51.5074) < 0.1 and abs(lon + 0.1278) < 0.1:  # London area
                    base_traffic_count = int(base_traffic_count * 1.4)
                    location_name = "London"
                elif abs(lat - 35.6762) < 0.1 and abs(lon - 139.6503) < 0.1:  # Tokyo area
                    base_traffic_count = int(base_traffic_count * 1.6)
                    location_name = "Tokyo"
                
                log_info(f"🚦 Dynamic traffic count: {base_traffic_count} (hour: {current_hour}, location: {location_name})")
                
                if tool_name == "get_current_traffic":
                    data = await fetch_live_traffic_data(lat, lon, count=base_traffic_count)
                elif tool_name == "get_historical_traffic":
                    # Historical mode shows more data points
                    historical_count = int(base_traffic_count * 1.5)
                    data = await fetch_live_traffic_data(lat, lon, count=historical_count)
                    # Adjust timestamps for historical simulation
                    start_time_arg = arguments.get("start_time")
                    if start_time_arg:
                        try:
                            start = datetime.fromisoformat(start_time_arg.replace('Z', '+00:00'))
                            for i, item in enumerate(data):
                                timestamp = start + timedelta(minutes=i * 30)
                                item["timestamp"] = timestamp.isoformat()
                        except Exception as e:
                            log_warning(f"Failed to adjust timestamps: {e}")
                else:
                    error_msg = f"Unknown traffic tool: {tool_name}"
                    log_error(error_msg)
                    raise ValueError(error_msg)
                
                duration_ms = (time.time() - start_time) * 1000
                log_mcp_call(
                    server_name=server_name,
                    tool_name=tool_name,
                    arguments=arguments,
                    success=True,
                    duration_ms=duration_ms,
                    result_count=len(data)
                )
                return data
                
            elif server_name == "restaurant-data":
                from mcp_servers.restaurant_server import parse_coordinates, fetch_live_restaurant_data
                
                zone_id = arguments.get("zone_id", "zone_1")
                lat, lon = parse_coordinates(zone_id)
                
                # Calculate dynamic count based on time and location
                current_hour = datetime.now().hour
                
                # Base restaurant count varies by meal times
                if 7 <= current_hour <= 11:  # Breakfast
                    base_restaurant_count = random.randint(8, 18)
                elif 12 <= current_hour <= 14:  # Lunch
                    base_restaurant_count = random.randint(20, 35)
                elif 18 <= current_hour <= 22:  # Dinner
                    base_restaurant_count = random.randint(25, 45)
                elif 22 <= current_hour or current_hour <= 6:  # Late night/early morning
                    base_restaurant_count = random.randint(3, 12)
                else:  # Off-peak hours
                    base_restaurant_count = random.randint(10, 20)
                
                # Add location-based variation (busy areas have more restaurants)
                location_name = "Unknown"
                if abs(lat - 40.7589) < 0.1 and abs(lon + 73.9851) < 0.1:  # NYC area
                    base_restaurant_count = int(base_restaurant_count * 1.8)
                    location_name = "NYC"
                elif abs(lat - 51.5074) < 0.1 and abs(lon + 0.1278) < 0.1:  # London area
                    base_restaurant_count = int(base_restaurant_count * 1.6)
                    location_name = "London"
                elif abs(lat - 35.6762) < 0.1 and abs(lon - 139.6503) < 0.1:  # Tokyo area
                    base_restaurant_count = int(base_restaurant_count * 1.7)
                    location_name = "Tokyo"
                
                log_info(f"🍽️ Dynamic restaurant count: {base_restaurant_count} (hour: {current_hour}, location: {location_name})")
                
                if tool_name == "get_current_reservations":
                    data = await fetch_live_restaurant_data(lat, lon, count=base_restaurant_count)
                elif tool_name == "get_historical_reservations":
                    # Historical mode shows more data points
                    historical_count = int(base_restaurant_count * 1.3)
                    data = await fetch_live_restaurant_data(lat, lon, count=historical_count)
                    # Adjust timestamps for historical simulation
                    start_time_arg = arguments.get("start_time")
                    if start_time_arg:
                        try:
                            start = datetime.fromisoformat(start_time_arg.replace('Z', '+00:00'))
                            for i, item in enumerate(data):
                                timestamp = start + timedelta(minutes=i * 30)
                                item["timestamp"] = timestamp.isoformat()
                        except Exception as e:
                            log_warning(f"Failed to adjust timestamps: {e}")
                else:
                    error_msg = f"Unknown restaurant tool: {tool_name}"
                    log_error(error_msg)
                    raise ValueError(error_msg)
                
                duration_ms = (time.time() - start_time) * 1000
                log_mcp_call(
                    server_name=server_name,
                    tool_name=tool_name,
                    arguments=arguments,
                    success=True,
                    duration_ms=duration_ms,
                    result_count=len(data)
                )
                return data
            
            else:
                error_msg = f"Unknown server: {server_name}"
                log_error(error_msg)
                raise ValueError(error_msg)
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Failed to call MCP tool {tool_name}: {str(e)}"
            log_mcp_call(
                server_name=server_name,
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                duration_ms=duration_ms,
                error=error_msg
            )
            raise RuntimeError(error_msg)
    
    async def get_current_traffic(self, zone_id: str) -> list[TrafficDataPoint]:
        """
        Fetch current traffic data via MCP.
        
        Args:
            zone_id: Geographic zone identifier
            
        Returns:
            List of traffic data points
        """
        try:
            log_info(f"Fetching current traffic data for zone: {zone_id}")
            
            data = await self.call_tool_direct(
                "traffic-data",
                "get_current_traffic",
                {"zone_id": zone_id}
            )
            
            if not data:
                log_warning(f"No traffic data returned for zone: {zone_id}")
                return []
            
            # Parse and validate data
            traffic_points = []
            for item in data:
                # Convert timestamp string to datetime if needed
                if isinstance(item.get('timestamp'), str):
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                traffic_points.append(TrafficDataPoint(**item))
            
            log_info(f"Successfully parsed {len(traffic_points)} traffic data points")
            return traffic_points
            
        except Exception as e:
            error_msg = f"MCP Traffic Error: {str(e)}"
            log_error(error_msg)
            raise RuntimeError(error_msg)
    
    async def get_historical_traffic(
        self,
        zone_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> list[TrafficDataPoint]:
        """
        Fetch historical traffic data via MCP.
        
        Args:
            zone_id: Geographic zone identifier
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of traffic data points
        """
        try:
            log_info(f"Fetching historical traffic data for zone: {zone_id}, "
                    f"time range: {start_time} to {end_time}")
            
            data = await self.call_tool_direct(
                "traffic-data",
                "get_historical_traffic",
                {
                    "zone_id": zone_id,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            )
            
            if not data:
                log_warning(f"No historical traffic data returned for zone: {zone_id}")
                return []
            
            traffic_points = []
            for item in data:
                # Convert timestamp string to datetime if needed
                if isinstance(item.get('timestamp'), str):
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                traffic_points.append(TrafficDataPoint(**item))
            
            log_info(f"Successfully parsed {len(traffic_points)} historical traffic data points")
            return traffic_points
            
        except Exception as e:
            error_msg = f"MCP Historical Traffic Error: {str(e)}"
            log_error(error_msg)
            raise RuntimeError(error_msg)
    
    async def get_current_reservations(self, zone_id: str) -> list[RestaurantDataPoint]:
        """
        Fetch current restaurant reservations via MCP.
        
        Args:
            zone_id: Geographic zone identifier
            
        Returns:
            List of restaurant data points
        """
        try:
            log_info(f"Fetching current restaurant reservations for zone: {zone_id}")
            
            data = await self.call_tool_direct(
                "restaurant-data",
                "get_current_reservations",
                {"zone_id": zone_id}
            )
            
            if not data:
                log_warning(f"No restaurant data returned for zone: {zone_id}")
                return []
            
            restaurant_points = []
            for item in data:
                # Convert timestamp string to datetime if needed
                if isinstance(item.get('timestamp'), str):
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                restaurant_points.append(RestaurantDataPoint(**item))
            
            log_info(f"Successfully parsed {len(restaurant_points)} restaurant data points")
            return restaurant_points
            
        except Exception as e:
            error_msg = f"MCP Restaurant Error: {str(e)}"
            log_error(error_msg)
            raise RuntimeError(error_msg)
    
    async def get_historical_reservations(
        self,
        zone_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> list[RestaurantDataPoint]:
        """
        Fetch historical reservation data via MCP.
        
        Args:
            zone_id: Geographic zone identifier
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of restaurant data points
        """
        try:
            log_info(f"Fetching historical restaurant reservations for zone: {zone_id}, "
                    f"time range: {start_time} to {end_time}")
            
            data = await self.call_tool_direct(
                "restaurant-data",
                "get_historical_reservations",
                {
                    "zone_id": zone_id,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
            )
            
            if not data:
                log_warning(f"No historical restaurant data returned for zone: {zone_id}")
                return []
            
            restaurant_points = []
            for item in data:
                # Convert timestamp string to datetime if needed
                if isinstance(item.get('timestamp'), str):
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                restaurant_points.append(RestaurantDataPoint(**item))
            
            log_info(f"Successfully parsed {len(restaurant_points)} historical restaurant data points")
            return restaurant_points
            
        except Exception as e:
            error_msg = f"MCP Historical Restaurant Error: {str(e)}"
            log_error(error_msg)
            raise RuntimeError(error_msg)
    
    async def close(self) -> None:
        """Close MCP client (simplified version)."""
        log_info("MCP Client: Closing connections")
        pass  # No persistent connections to close
