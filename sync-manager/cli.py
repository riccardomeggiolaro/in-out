#!/usr/bin/env python3
"""
Sync Manager CLI - Command Line Interface
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.prompt import Confirm, Prompt
from rich import print as rprint

console = Console()


class SyncManagerCLI:
    """CLI client for Sync Manager"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    async def request(self, method: str, endpoint: str, **kwargs):
        """Make API request"""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}/api/v1{endpoint}",
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.text else None


@click.group()
@click.option('--api-url', envvar='SYNC_API_URL', default='http://localhost:8000', help='API base URL')
@click.option('--api-key', envvar='SYNC_API_KEY', help='API key for authentication')
@click.pass_context
def cli(ctx, api_url, api_key):
    """Sync Manager CLI - Manage file synchronizations from the command line"""
    ctx.ensure_object(dict)
    ctx.obj['client'] = SyncManagerCLI(api_url, api_key)


# ==================== Sync Commands ====================

@cli.group()
def sync():
    """Manage sync configurations"""
    pass


@sync.command('list')
@click.option('--enabled-only', is_flag=True, help='Show only enabled syncs')
@click.option('--format', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def list_syncs(ctx, enabled_only, format):
    """List all sync configurations"""
    
    async def _list():
        client = ctx.obj['client']
        syncs = await client.request('GET', '/syncs', params={'enabled_only': enabled_only})
        
        if format == 'json':
            console.print_json(json.dumps(syncs))
        else:
            table = Table(title="Sync Configurations")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Source", style="green")
            table.add_column("Destination", style="yellow")
            table.add_column("Status", style="bold")
            table.add_column("Enabled", style="bold")
            
            for sync in syncs:
                table.add_row(
                    str(sync['id']),
                    sync['name'],
                    sync['source_path'],
                    sync['destination_path'],
                    sync['status'],
                    "✓" if sync['enabled'] else "✗"
                )
            
            console.print(table)
    
    asyncio.run(_list())


@sync.command('create')
@click.option('--name', prompt=True, help='Sync configuration name')
@click.option('--source', prompt=True, help='Source directory path')
@click.option('--destination', prompt=True, help='Destination directory path')
@click.option('--delete-after', is_flag=True, help='Delete files after sync')
@click.option('--interval', default=5, help='Sync interval in seconds')
@click.option('--enabled/--disabled', default=True, help='Enable sync immediately')
@click.pass_context
def create_sync(ctx, name, source, destination, delete_after, interval, enabled):
    """Create a new sync configuration"""
    
    async def _create():
        client = ctx.obj['client']
        
        config = {
            "name": name,
            "source_path": source,
            "destination_path": destination,
            "delete_after_sync": delete_after,
            "sync_interval": interval,
            "enabled": enabled
        }
        
        with console.status("[bold green]Creating sync configuration..."):
            result = await client.request('POST', '/syncs', json=config)
        
        console.print(f"[bold green]✓[/] Created sync: {result['name']} (ID: {result['id']})")
        
        if enabled:
            console.print(f"[bold blue]ℹ[/] Sync will start automatically")
    
    asyncio.run(_create())


@sync.command('show')
@click.argument('sync_id', type=int)
@click.option('--format', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def show_sync(ctx, sync_id, format):
    """Show details of a sync configuration"""
    
    async def _show():
        client = ctx.obj['client']
        sync = await client.request('GET', f'/syncs/{sync_id}')
        
        if format == 'json':
            console.print_json(json.dumps(sync))
        else:
            console.print(f"\n[bold]Sync Configuration #{sync['id']}[/bold]")
            console.print(f"Name: {sync['name']}")
            console.print(f"Description: {sync.get('description', 'N/A')}")
            console.print(f"Source: {sync['source_path']} ({sync['source_type']})")
            console.print(f"Destination: {sync['destination_path']} ({sync['destination_type']})")
            console.print(f"Status: [bold]{sync['status']}[/bold]")
            console.print(f"Enabled: {'✓' if sync['enabled'] else '✗'}")
            console.print(f"Delete after sync: {'Yes' if sync['delete_after_sync'] else 'No'}")
            console.print(f"Sync interval: {sync['sync_interval']}s")
            console.print(f"Total files synced: {sync['total_files_synced']}")
            console.print(f"Total bytes synced: {sync['total_bytes_synced']:,.0f}")
            console.print(f"Created: {sync['created_at']}")
            console.print(f"Last sync: {sync.get('last_sync', 'Never')}")
    
    asyncio.run(_show())


@sync.command('update')
@click.argument('sync_id', type=int)
@click.option('--name', help='New name')
@click.option('--source', help='New source path')
@click.option('--destination', help='New destination path')
@click.option('--interval', type=int, help='New sync interval')
@click.option('--enable/--disable', default=None, help='Enable or disable sync')
@click.pass_context
def update_sync(ctx, sync_id, name, source, destination, interval, enable):
    """Update a sync configuration"""
    
    async def _update():
        client = ctx.obj['client']
        
        updates = {}
        if name:
            updates['name'] = name
        if source:
            updates['source_path'] = source
        if destination:
            updates['destination_path'] = destination
        if interval:
            updates['sync_interval'] = interval
        if enable is not None:
            updates['enabled'] = enable
        
        if not updates:
            console.print("[yellow]No updates specified[/]")
            return
        
        with console.status(f"[bold green]Updating sync {sync_id}..."):
            result = await client.request('PUT', f'/syncs/{sync_id}', json=updates)
        
        console.print(f"[bold green]✓[/] Updated sync: {result['name']}")
    
    asyncio.run(_update())


@sync.command('delete')
@click.argument('sync_id', type=int)
@click.option('--force', is_flag=True, help='Skip confirmation')
@click.pass_context
def delete_sync(ctx, sync_id, force):
    """Delete a sync configuration"""
    
    async def _delete():
        client = ctx.obj['client']
        
        if not force:
            if not Confirm.ask(f"Are you sure you want to delete sync {sync_id}?"):
                return
        
        with console.status(f"[bold red]Deleting sync {sync_id}..."):
            await client.request('DELETE', f'/syncs/{sync_id}')
        
        console.print(f"[bold green]✓[/] Deleted sync {sync_id}")
    
    asyncio.run(_delete())


# ==================== Control Commands ====================

@cli.group()
def control():
    """Control sync operations"""
    pass


@control.command('start')
@click.argument('sync_id', type=int)
@click.pass_context
def start_sync(ctx, sync_id):
    """Start a sync operation"""
    
    async def _start():
        client = ctx.obj['client']
        
        with console.status(f"[bold green]Starting sync {sync_id}..."):
            result = await client.request('POST', f'/syncs/{sync_id}/start')
        
        console.print(f"[bold green]✓[/] Sync {sync_id} started")
        console.print(f"Status: {result['status']}")
    
    asyncio.run(_start())


@control.command('stop')
@click.argument('sync_id', type=int)
@click.pass_context
def stop_sync(ctx, sync_id):
    """Stop a sync operation"""
    
    async def _stop():
        client = ctx.obj['client']
        
        with console.status(f"[bold yellow]Stopping sync {sync_id}..."):
            result = await client.request('POST', f'/syncs/{sync_id}/stop')
        
        console.print(f"[bold green]✓[/] Sync {sync_id} stopped")
        console.print(f"Status: {result['status']}")
    
    asyncio.run(_stop())


@control.command('force')
@click.argument('sync_id', type=int)
@click.pass_context
def force_sync(ctx, sync_id):
    """Force immediate sync"""
    
    async def _force():
        client = ctx.obj['client']
        
        with console.status(f"[bold blue]Forcing sync {sync_id}..."):
            result = await client.request('POST', f'/syncs/{sync_id}/force')
        
        console.print(f"[bold green]✓[/] {result['message']}")
    
    asyncio.run(_force())


# ==================== Status Commands ====================

@cli.group()
def status():
    """Monitor sync status"""
    pass


@status.command('show')
@click.argument('sync_id', type=int, required=False)
@click.pass_context
def show_status(ctx, sync_id):
    """Show sync status"""
    
    async def _status():
        client = ctx.obj['client']
        
        if sync_id:
            status = await client.request('GET', f'/syncs/{sync_id}/status')
            
            console.print(f"\n[bold]Sync #{status['id']}: {status['name']}[/bold]")
            console.print(f"Status: [bold]{status['status']}[/bold]")
            console.print(f"Running: {'Yes' if status['is_running'] else 'No'}")
            console.print(f"Queue size: {status.get('queue_size', 0)}")
            console.print(f"Retry queue: {status.get('retry_queue_size', 0)}")
            console.print(f"Last sync: {status.get('last_sync', 'Never')}")
            
            if status.get('stats'):
                stats = status['stats']
                console.print(f"\n[bold]Statistics:[/bold]")
                console.print(f"Files synced: {stats.get('files_synced', 0)}")
                console.print(f"Bytes synced: {stats.get('bytes_synced', 0):,.0f}")
                console.print(f"Errors: {stats.get('errors', 0)}")
        else:
            # Show all status
            statuses = await client.request('GET', '/status')
            
            table = Table(title="Sync Status")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Status", style="bold")
            table.add_column("Running", style="bold")
            table.add_column("Queue", style="yellow")
            table.add_column("Last Sync")
            
            for s in statuses:
                table.add_row(
                    str(s['id']),
                    s['name'],
                    s['status'],
                    "✓" if s['is_running'] else "✗",
                    str(s.get('queue_size', 0)),
                    s.get('last_sync', 'Never')[:19] if s.get('last_sync') else 'Never'
                )
            
            console.print(table)
    
    asyncio.run(_status())


@status.command('metrics')
@click.pass_context
def show_metrics(ctx):
    """Show system metrics"""
    
    async def _metrics():
        client = ctx.obj['client']
        metrics = await client.request('GET', '/metrics')
        
        console.print("\n[bold]System Metrics[/bold]")
        console.print(f"Active syncs: {metrics['active_syncs']}")
        console.print(f"Files in queue: {metrics['files_in_queue']}")
        console.print(f"Files synced today: {metrics['files_synced_today']}")
        console.print(f"Bytes synced today: {metrics['bytes_synced_today']:,.0f}")
        console.print(f"CPU usage: {metrics.get('cpu_usage', 'N/A')}%")
        console.print(f"Memory usage: {metrics.get('memory_usage', 'N/A')}%")
        console.print(f"Disk usage: {metrics.get('disk_usage', 'N/A')}%")
    
    asyncio.run(_metrics())


@status.command('health')
@click.pass_context
def health_check(ctx):
    """Check system health"""
    
    async def _health():
        client = ctx.obj['client']
        
        try:
            health = await client.request('GET', '/health')
            
            if health['status'] == 'healthy':
                console.print(f"[bold green]✓ System is healthy[/]")
            else:
                console.print(f"[bold red]✗ System is unhealthy[/]")
            
            console.print(f"\nVersion: {health['version']}")
            console.print("Component checks:")
            for component, status in health['checks'].items():
                emoji = "✓" if "healthy" in status else "✗"
                console.print(f"  {emoji} {component}: {status}")
        except Exception as e:
            console.print(f"[bold red]✗ Health check failed: {e}[/]")
    
    asyncio.run(_health())


@status.command('history')
@click.argument('sync_id', type=int)
@click.option('--limit', default=10, help='Number of entries to show')
@click.pass_context
def show_history(ctx, sync_id, limit):
    """Show sync history"""
    
    async def _history():
        client = ctx.obj['client']
        history = await client.request('GET', f'/syncs/{sync_id}/history', params={'limit': limit})
        
        if not history:
            console.print("No history entries")
            return
        
        table = Table(title=f"Sync History (#{sync_id})")
        table.add_column("Time", style="cyan")
        table.add_column("Operation", style="magenta")
        table.add_column("File", style="yellow")
        table.add_column("Result", style="bold")
        
        for entry in history:
            table.add_row(
                entry['timestamp'][:19],
                entry['operation'],
                Path(entry['file_path']).name if entry.get('file_path') else '-',
                "✓" if entry['success'] else f"✗ {entry.get('error_message', '')}"
            )
        
        console.print(table)
    
    asyncio.run(_history())


# ==================== Interactive Mode ====================

@cli.command('interactive')
@click.pass_context
def interactive_mode(ctx):
    """Start interactive mode"""
    console.print("[bold]Sync Manager Interactive Mode[/bold]")
    console.print("Type 'help' for available commands, 'exit' to quit\n")
    
    commands = {
        'list': 'List all syncs',
        'show <id>': 'Show sync details',
        'start <id>': 'Start a sync',
        'stop <id>': 'Stop a sync',
        'status': 'Show all sync status',
        'metrics': 'Show system metrics',
        'health': 'Check system health',
        'help': 'Show this help',
        'exit': 'Exit interactive mode'
    }
    
    while True:
        try:
            cmd = Prompt.ask("\n[bold blue]sync-manager>[/]").strip()
            
            if not cmd:
                continue
            
            if cmd == 'exit':
                console.print("Goodbye!")
                break
            
            if cmd == 'help':
                console.print("\n[bold]Available commands:[/bold]")
                for cmd_name, desc in commands.items():
                    console.print(f"  {cmd_name:15} - {desc}")
                continue
            
            # Parse command
            parts = cmd.split()
            command = parts[0]
            args = parts[1:] if len(parts) > 1 else []
            
            # Execute command
            if command == 'list':
                ctx.invoke(list_syncs, enabled_only=False, format='table')
            elif command == 'show' and args:
                ctx.invoke(show_sync, sync_id=int(args[0]), format='table')
            elif command == 'start' and args:
                ctx.invoke(start_sync, sync_id=int(args[0]))
            elif command == 'stop' and args:
                ctx.invoke(stop_sync, sync_id=int(args[0]))
            elif command == 'status':
                ctx.invoke(show_status, sync_id=None)
            elif command == 'metrics':
                ctx.invoke(show_metrics)
            elif command == 'health':
                ctx.invoke(health_check)
            else:
                console.print(f"[red]Unknown command: {command}[/]")
                console.print("Type 'help' for available commands")
                
        except KeyboardInterrupt:
            console.print("\nUse 'exit' to quit")
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")


def main():
    """Main entry point"""
    cli(obj={})


if __name__ == '__main__':
    main()
