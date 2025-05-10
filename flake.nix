{
  description = "Bible Reading Plan Schema validator";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-23.11"; # Using a more stable/older release
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python311;
      in
      {
        packages = {
          default = pkgs.python311Packages.buildPythonApplication {
            pname = "bible-reading-plan-schema";
            version = "0.1.0";
            src = ./.;
            
            propagatedBuildInputs = with pkgs.python311Packages; [
              pyyaml
              setuptools
              wheel
            ];
            
            # Since we don't have a proper Python package structure with setup.py,
            # we need to customize some phases
            format = "other";
            
            installPhase = ''
              runHook preInstall
              
              mkdir -p $out/${python.sitePackages}/scripts
              mkdir -p $out/bin
              
              cp -r scripts/validate_reading_plan.py $out/${python.sitePackages}/scripts/
              cp books-of-the-bible.yaml $out/${python.sitePackages}/
              
              # Create a wrapper script
              cat > $out/bin/validate-reading-plan << EOF
              #!/bin/sh
              PYTHONPATH=$out/${python.sitePackages}:$PYTHONPATH exec python -m scripts.validate_reading_plan "\$@"
              EOF
              
              chmod +x $out/bin/validate-reading-plan
              
              runHook postInstall
            '';
            
            meta = with pkgs.lib; {
              description = "Schema and validation tools for Bible reading plans";
              homepage = "https://github.com/yourusername/bible-reading-plan-schema";
              license = licenses.mit;
            };
          };
        };
        
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = [
            (python.withPackages (ps: with ps; [
              pyyaml
              setuptools
              wheel
            ]))
            pkgs.yaml-language-server
          ];
          
          shellHook = ''
            echo "Bible Reading Plan Schema Environment"
            echo "==================================="
            echo "Python version:"
            python --version
            echo ""
            echo "Available commands:"
            echo "  python -m scripts.validate_reading_plan [file]  - Validate a specific plan file"
            echo ""
          '';
        };
        
        # Add a simple app that can be run with 'nix run'
        apps.default = flake-utils.lib.mkApp {
          drv = self.packages.${system}.default;
          name = "validate-reading-plan";
        };
      });
}