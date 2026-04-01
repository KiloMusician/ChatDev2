{
  description = "CoreLink Foundation - Culture-ship Level Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          name = "corelink-foundation-dev";

          buildInputs = with pkgs; [
            # Node.js ecosystem
            nodejs_20
            nodePackages.npm
            nodePackages.typescript
            nodePackages.ts-node

            # Database & Storage
            postgresql_15
            redis

            # AI/ML Development
            ollama
            python311
            python311Packages.pip
            python311Packages.numpy
            python311Packages.pandas

            # Game Development Tools
            godot_4
            imagemagick
            ffmpeg

            # Development Tools
            git
            curl
            jq
            tree
            ripgrep
            fd
            bat
            
            # UI/UX Design Tools
            figma-linux
            inkscape
            gimp

            # Performance & Monitoring
            htop
            iotop
            nethogs
          ];

          shellHook = ''
            echo "🚀 CoreLink Foundation Development Environment"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "🧠 ΞNuSyQ Framework: Autonomous AI Development"
            echo "🎮 Game Engine: React + TypeScript + Vite"
            echo "🗄️  Database: PostgreSQL 15"
            echo "🤖 AI Models: Ollama (Local, Zero-cost)"
            echo "🎨 Design Tools: Figma, Inkscape, GIMP"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            
            # Set up environment variables
            export CORELINK_ENV="development"
            export DATABASE_URL="postgresql://localhost:5432/corelink_dev"
            export OLLAMA_HOST="http://localhost:11434"
            
            # Create dev directories if they don't exist
            mkdir -p .dev-env/{logs,cache,assets}
            
            # Initialize database if needed
            if ! pg_isready -q; then
              echo "🔧 Starting PostgreSQL..."
              pg_ctl -D ~/.postgres -l ~/.postgres/logfile start
            fi
            
            echo "✅ Development environment ready!"
            echo "📁 Run 'npm run dev' to start the application"
            echo "🎨 Run 'npm run design' for UI development mode"
            echo "🧠 Run 'npm run ai' for AI/ML development"
          '';

          # Environment variables for development
          NIXOS_OZONE_WL = "1"; # Wayland support
          QT_QPA_PLATFORM = "wayland";
          GDK_BACKEND = "wayland";
        };

        # Additional development shells for specialized work
        devShells.design = pkgs.mkShell {
          name = "corelink-design";
          buildInputs = with pkgs; [
            nodejs_20
            figma-linux
            inkscape
            gimp
            krita
            blender
            godot_4
          ];
          shellHook = ''
            echo "🎨 CoreLink Foundation - Design Environment"
            echo "Ready for UI/UX design and asset creation!"
          '';
        };

        devShells.ai = pkgs.mkShell {
          name = "corelink-ai";
          buildInputs = with pkgs; [
            python311
            python311Packages.pip
            python311Packages.numpy
            python311Packages.pandas
            python311Packages.matplotlib
            python311Packages.jupyter
            ollama
            nodejs_20
          ];
          shellHook = ''
            echo "🧠 CoreLink Foundation - AI Development Environment"
            echo "Ready for ΞNuSyQ framework development!"
          '';
        };
      });
}