#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Display help message
show_help() {
    echo "Pathy Roadmap AI Starter Script"
    echo ""
    echo "Usage: ./start.sh [command]"
    echo ""
    echo "Commands:"
    echo "  dev         Start both services locally for development"
    echo "  docker      Build and start both services in Docker container (VPS ready)"
    echo "  docker-dev  Build and start both services in Docker with Hot-Reloading for development"
    echo "  stop        Stop Docker containers"
    echo "  help        Show this help message"
    echo ""
}

# Run services locally in dev mode
run_dev() {
    echo "🚀 Starting development servers..."

    # Check for .env file
    if [ ! -f .env ]; then
        echo "⚠️  .env file not found! Copying .env.example..."
        cp .env.example .env
        echo "👉 Please fill in your API keys in the .env file."
    fi

    # Start backend in background
    echo "🐍 Starting Python backend..."
    uv run python server.py &
    BACKEND_PID=$!

    # Start frontend
    echo "📦 Starting Next.js frontend..."
    cd agentui
    
    # Clear Next.js cache to prevent routes-manifest.json errors
    rm -rf .next
    
    # Automatically select package manager
    if command -v bun &> /dev/null; then
        echo "⚡ Using Bun..."
        bun dev &
    elif [ -f pnpm-lock.yaml ] && command -v pnpm &> /dev/null; then
        echo "📦 Using PNPM..."
        pnpm run dev &
    else
        echo "📦 Using NPM..."
        npm run dev &
    fi
    FRONTEND_PID=$!

    # Go back to root and handle termination
    cd ..
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

    # Wait for both processes
    wait
}

# Run services in Docker
run_docker() {
    echo "🐋 Starting Pathy Roadmap AI in Docker..."
    
    # Check for .env file
    if [ ! -f .env ]; then
        echo "❌ Error: .env file is required to run Docker!"
        echo "👉 Copy .env.example to .env and fill in your API keys first."
        exit 1
    fi

    docker compose up --build
}

# Run services in Docker Dev Mode
run_docker_dev() {
    echo "🐋 Starting Pathy Roadmap AI in Docker (Development Mode with Hot-Reloading)..."
    
    # Check for .env file
    if [ ! -f .env ]; then
        echo "❌ Error: .env file is required to run Docker!"
        echo "👉 Copy .env.example to .env and fill in your API keys first."
        exit 1
    fi

    docker compose -f docker-compose.dev.yml up --build
}

# Stop Docker containers
stop_docker() {
    echo "🛑 Stopping Docker containers..."
    docker compose down
    docker compose -f docker-compose.dev.yml down 2>/dev/null || true
}

# Parse command line arguments
case "$1" in
    dev)
        run_dev
        ;;
    docker)
        run_docker
        ;;
    docker-dev)
        run_docker_dev
        ;;
    stop)
        stop_docker
        ;;
    *)
        show_help
        ;;
esac
