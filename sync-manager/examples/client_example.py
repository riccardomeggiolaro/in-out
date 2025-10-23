#!/usr/bin/env python3
"""
Sync Manager API Client Example

This script demonstrates how to use the Sync Manager API
to create, manage, and monitor file synchronizations.
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Optional, Dict, List, Any

import httpx
import websockets


class SyncManagerClient:
    """Client for Sync Manager API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    # ==================== Sync Configuration ====================
    
    async def create_sync(self, config: Dict[str, Any]) -> Dict:
        """Create a new sync configuration"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/syncs",
                json=config,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def list_syncs(self, enabled_only: bool = False) -> List[Dict]:
        """List all sync configurations"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/syncs",
                params={"enabled_only": enabled_only},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_sync(self, sync_id: int) -> Dict:
        """Get a specific sync configuration"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/syncs/{sync_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def update_sync(self, sync_id: int, updates: Dict[str, Any]) -> Dict:
        """Update a sync configuration"""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/api/v1/syncs/{sync_id}",
                json=updates,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_sync(self, sync_id: int) -> Dict:
        """Delete a sync configuration"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/v1/syncs/{sync_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    # ==================== Sync Control ====================
    
    async def start_sync(self, sync_id: int) -> Dict:
        """Start a sync operation"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/syncs/{sync_id}/start",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def stop_sync(self, sync_id: int) -> Dict:
        """Stop a sync operation"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/syncs/{sync_id}/stop",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def force_sync(self, sync_id: int) -> Dict:
        """Force immediate sync"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/syncs/{sync_id}/force",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    # ==================== Status and Monitoring ====================
    
    async def get_sync_status(self, sync_id: int) -> Dict:
        """Get sync status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/syncs/{sync_id}/status",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_all_status(self) -> List[Dict]:
        """Get status of all syncs"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/status",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_sync_history(self, sync_id: int, limit: int = 100) -> List[Dict]:
        """Get sync history"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/syncs/{sync_id}/history",
                params={"limit": limit},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_metrics(self) -> Dict:
        """Get system metrics"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/metrics",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> Dict:
        """Check system health"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/health",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    # ==================== WebSocket ====================
    
    async def connect_websocket(self, on_message=None):
        """Connect to WebSocket for real-time updates"""
        ws_url = self.base_url.replace("http", "ws") + "/ws"
        
        async with websockets.connect(ws_url) as websocket:
            print(f"Connected to WebSocket: {ws_url}")
            
            # Subscribe to events
            await websocket.send(json.dumps({
                "type": "subscribe",
                "events": ["sync_event", "file_event", "system_event"]
            }))
            
            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                
                if on_message:
                    on_message(data)
                else:
                    print(f"WebSocket message: {data}")


# ==================== Example Usage ====================

async def example_basic_usage():
    """Example of basic API usage"""
    
    # Create client
    client = SyncManagerClient()
    
    print("=" * 60)
    print("SYNC MANAGER API CLIENT EXAMPLE")
    print("=" * 60)
    
    try:
        # 1. Check health
        print("\n1. Checking system health...")
        health = await client.health_check()
        print(f"   Health: {health['status']}")
        
        # 2. Create a new sync
        print("\n2. Creating new sync configuration...")
        sync_config = {
            "name": "Documents Backup",
            "description": "Backup local documents to NAS",
            "source_path": "/home/user/documents",
            "destination_path": "/mnt/nas/backup/documents",
            "enabled": True,
            "delete_after_sync": False,  # Keep originals
            "sync_interval": 300,  # 5 minutes
            "exclude_patterns": ["*.tmp", "*.lock", "~*"]
        }
        
        new_sync = await client.create_sync(sync_config)
        sync_id = new_sync["id"]
        print(f"   Created sync: {new_sync['name']} (ID: {sync_id})")
        
        # 3. Start the sync
        print(f"\n3. Starting sync {sync_id}...")
        status = await client.start_sync(sync_id)
        print(f"   Status: {status['status']}")
        
        # 4. Get current status
        print(f"\n4. Getting sync status...")
        status = await client.get_sync_status(sync_id)
        print(f"   Running: {status['is_running']}")
        print(f"   Queue size: {status.get('queue_size', 0)}")
        
        # 5. List all syncs
        print("\n5. Listing all syncs...")
        syncs = await client.list_syncs()
        for sync in syncs:
            print(f"   - {sync['name']} (ID: {sync['id']}) - {sync['status']}")
        
        # 6. Get metrics
        print("\n6. Getting system metrics...")
        metrics = await client.get_metrics()
        print(f"   Active syncs: {metrics['active_syncs']}")
        print(f"   Files in queue: {metrics['files_in_queue']}")
        print(f"   CPU usage: {metrics.get('cpu_usage', 'N/A')}%")
        
        # 7. Force sync
        print(f"\n7. Forcing immediate sync for {sync_id}...")
        result = await client.force_sync(sync_id)
        print(f"   {result['message']}")
        
        # 8. Get history
        print(f"\n8. Getting sync history...")
        history = await client.get_sync_history(sync_id, limit=5)
        for entry in history[:3]:
            print(f"   - {entry['timestamp']}: {entry['operation']} - {'✓' if entry['success'] else '✗'}")
        
        # 9. Update configuration
        print(f"\n9. Updating sync configuration...")
        updates = {
            "sync_interval": 600,  # Change to 10 minutes
            "enabled": True
        }
        updated = await client.update_sync(sync_id, updates)
        print(f"   Updated interval to: {updated['sync_interval']}s")
        
        # 10. Stop sync
        print(f"\n10. Stopping sync {sync_id}...")
        status = await client.stop_sync(sync_id)
        print(f"    Status: {status['status']}")
        
    except httpx.HTTPError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Error: {e}")


async def example_advanced_usage():
    """Example of advanced API usage with multiple syncs"""
    
    client = SyncManagerClient()
    
    print("\n" + "=" * 60)
    print("ADVANCED EXAMPLE - MULTIPLE SYNCS")
    print("=" * 60)
    
    # Create multiple sync configurations
    sync_configs = [
        {
            "name": "Photos Backup",
            "source_path": "/home/user/photos",
            "destination_path": "/mnt/nas/photos",
            "delete_after_sync": False,
            "include_patterns": ["*.jpg", "*.png", "*.raw"],
            "min_file_size": 1024,  # Skip files smaller than 1KB
        },
        {
            "name": "Project Sync",
            "source_path": "/home/user/projects",
            "destination_path": "/mnt/backup/projects",
            "delete_after_sync": True,
            "exclude_patterns": ["node_modules", "*.pyc", "__pycache__"],
        },
        {
            "name": "Downloads Cleanup",
            "source_path": "/home/user/downloads",
            "destination_path": "/mnt/archive/downloads",
            "delete_after_sync": True,
            "sync_interval": 3600,  # Every hour
            "max_file_size": 1073741824,  # Max 1GB files
        }
    ]
    
    created_syncs = []
    
    try:
        # Create all syncs
        for config in sync_configs:
            print(f"\nCreating sync: {config['name']}")
            sync = await client.create_sync(config)
            created_syncs.append(sync)
            print(f"  Created with ID: {sync['id']}")
        
        # Start all syncs
        print("\nStarting all syncs...")
        for sync in created_syncs:
            await client.start_sync(sync['id'])
            print(f"  Started: {sync['name']}")
        
        # Monitor status
        print("\nMonitoring sync status...")
        await asyncio.sleep(2)
        
        all_status = await client.get_all_status()
        for status in all_status:
            if status['is_running']:
                print(f"  {status['name']}:")
                print(f"    Status: {status['status']}")
                print(f"    Queue: {status.get('queue_size', 0)} files")
                if status.get('stats'):
                    print(f"    Synced: {status['stats'].get('files_synced', 0)} files")
        
        # Batch operation example
        print("\nStopping all syncs...")
        for sync in created_syncs:
            await client.stop_sync(sync['id'])
            print(f"  Stopped: {sync['name']}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Cleanup - delete created syncs
        print("\nCleaning up...")
        for sync in created_syncs:
            try:
                await client.delete_sync(sync['id'])
                print(f"  Deleted: {sync['name']}")
            except:
                pass


async def example_websocket():
    """Example of WebSocket connection for real-time updates"""
    
    client = SyncManagerClient()
    
    print("\n" + "=" * 60)
    print("WEBSOCKET EXAMPLE - REAL-TIME UPDATES")
    print("=" * 60)
    print("\nConnecting to WebSocket...")
    print("Press Ctrl+C to stop\n")
    
    def handle_message(data):
        """Handle incoming WebSocket message"""
        msg_type = data.get("type")
        
        if msg_type == "sync_event":
            print(f"[SYNC] {data['event']} - Sync ID: {data['sync_id']}")
        elif msg_type == "file_event":
            print(f"[FILE] {data['event']} - {data['file_path']}")
        elif msg_type == "system_event":
            print(f"[SYSTEM] {data['event']}")
        elif msg_type == "metrics":
            metrics = data['data']
            print(f"[METRICS] Active: {metrics['active_syncs']}, Queue: {metrics['files_in_queue']}")
        elif msg_type == "heartbeat":
            # Ignore heartbeats
            pass
        else:
            print(f"[{msg_type.upper()}] {data}")
    
    try:
        await client.connect_websocket(on_message=handle_message)
    except KeyboardInterrupt:
        print("\nWebSocket connection closed")
    except Exception as e:
        print(f"WebSocket error: {e}")


async def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "basic":
            await example_basic_usage()
        elif command == "advanced":
            await example_advanced_usage()
        elif command == "websocket":
            await example_websocket()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python client_example.py [basic|advanced|websocket]")
    else:
        # Run basic example by default
        await example_basic_usage()


if __name__ == "__main__":
    asyncio.run(main())
