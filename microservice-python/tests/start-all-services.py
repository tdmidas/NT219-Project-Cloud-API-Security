#!/usr/bin/env python3
"""
Start all Voux microservices (Python version)
"""

import subprocess
import sys
import time
import os
import argparse
from concurrent.futures import ThreadPoolExecutor
import requests
from typing import List, Dict

# Service configurations
SERVICES = {
    "auth-service": {
        "port": 3001,
        "dir": "auth-service",
        "module": "main:app"
    },
    "user-service": {
        "port": 3002,
        "dir": "user-service", 
        "module": "main:app"
    },
    "voucher-service": {
        "port": 3003,
        "dir": "voucher-service",
        "module": "main:app"
    },
    "cart-service": {
        "port": 3004,
        "dir": "cart-service",
        "module": "main:app"
    },
    "api-gateway": {
        "port": 8060,
        "dir": "api-gateway",
        "module": "main:app"
    }
}

def check_port_available(port: int) -> bool:
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def wait_for_service(service_name: str, port: int, timeout: int = 60) -> bool:
    """Wait for a service to be ready"""
    print(f"⏳ Waiting for {service_name} on port {port}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} is ready!")
                return True
        except requests.RequestException:
            pass
        
        time.sleep(2)
    
    print(f"❌ {service_name} failed to start within {timeout} seconds")
    return False

def start_service(service_name: str, config: Dict, dev_mode: bool = False) -> subprocess.Popen:
    """Start a single service"""
    print(f"🚀 Starting {service_name}...")
    
    # Check if port is available
    if not check_port_available(config["port"]):
        print(f"⚠️ Port {config['port']} is already in use for {service_name}")
        return None
    
    # Set environment variables
    env = os.environ.copy()
    env[f"{service_name.upper().replace('-', '_')}_PORT"] = str(config["port"])
    
    # Build uvicorn command
    cmd = [
        "python", "-m", "uvicorn",
        config["module"],
        "--host", "0.0.0.0",
        "--port", str(config["port"])
    ]
    
    if dev_mode:
        cmd.extend(["--reload", "--log-level", "debug"])
    
    # Start the service
    try:
        process = subprocess.Popen(
            cmd,
            cwd=config["dir"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        return process
        
    except Exception as e:
        print(f"❌ Failed to start {service_name}: {e}")
        return None

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import motor
        import pymongo
        import aio_pika  # RabbitMQ dependency
        print("✅ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Please run: pip install -r requirements.txt")
        return False

def check_environment():
    """Check environment setup"""
    print("🔍 Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {sys.version}")
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Check environment file
    if not os.path.exists(".env"):
        print("⚠️ .env file not found, using default environment variables")
        print("💡 Consider creating a .env file for custom configuration")
    else:
        print("✅ .env file found")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Start Voux microservices")
    parser.add_argument("--dev", action="store_true", help="Start in development mode with auto-reload")
    parser.add_argument("--install", action="store_true", help="Install dependencies before starting")
    parser.add_argument("--services", nargs="*", choices=list(SERVICES.keys()), 
                       help="Start specific services only")
    parser.add_argument("--wait", action="store_true", help="Wait for all services to be ready")
    
    args = parser.parse_args()
    
    print("🔥 Voux Microservices Launcher (Python)")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Install dependencies if requested
    if args.install:
        if not install_dependencies():
            sys.exit(1)
    
    # Determine which services to start
    services_to_start = args.services if args.services else list(SERVICES.keys())
    
    print(f"🎯 Starting services: {', '.join(services_to_start)}")
    
    # Start services
    processes = {}
    
    # Start services in dependency order
    service_order = ["auth-service", "user-service", "voucher-service", "cart-service", "api-gateway"]
    
    for service_name in service_order:
        if service_name in services_to_start:
            config = SERVICES[service_name]
            process = start_service(service_name, config, args.dev)
            
            if process:
                processes[service_name] = process
                time.sleep(2)  # Give service time to start
    
    if not processes:
        print("❌ No services were started")
        sys.exit(1)
    
    print(f"\n✅ Started {len(processes)} services")
    
    # Wait for services to be ready if requested
    if args.wait:
        print("\n⏳ Waiting for all services to be ready...")
        all_ready = True
        
        for service_name, process in processes.items():
            config = SERVICES[service_name]
            if not wait_for_service(service_name, config["port"]):
                all_ready = False
        
        if all_ready:
            print("\n🎉 All services are ready!")
        else:
            print("\n⚠️ Some services failed to start properly")
    
    # Print service information
    print("\n📋 Service Status:")
    print("-" * 50)
    
    for service_name, process in processes.items():
        config = SERVICES[service_name]
        status = "Running" if process.poll() is None else "Stopped"
        print(f"{service_name:15} | Port {config['port']:4} | {status}")
    
    print("\n🌐 Access URLs:")
    print("-" * 50)
    for service_name, process in processes.items():
        if process.poll() is None:  # Still running
            config = SERVICES[service_name]
            print(f"{service_name:15} | http://localhost:{config['port']}")
    
    if "api-gateway" in processes and processes["api-gateway"].poll() is None:
        print(f"\n🚪 API Gateway: http://localhost:{SERVICES['api-gateway']['port']}")
        print(f"📚 API Docs: http://localhost:{SERVICES['api-gateway']['port']}/docs")
    
    print("\n💡 Press Ctrl+C to stop all services")
    
    try:
        # Keep the script running and monitor processes
        while True:
            time.sleep(5)
            
            # Check if any process has died
            for service_name, process in list(processes.items()):
                if process.poll() is not None:
                    print(f"⚠️ {service_name} has stopped")
                    del processes[service_name]
            
            if not processes:
                print("🛑 All services have stopped")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        
        # Terminate all processes
        for service_name, process in processes.items():
            print(f"   Stopping {service_name}...")
            process.terminate()
        
        # Wait for processes to terminate
        for service_name, process in processes.items():
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {service_name}...")
                process.kill()
        
        print("✅ All services stopped")

if __name__ == "__main__":
    main() 