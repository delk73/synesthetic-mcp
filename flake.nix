{
  description = "Synesthetic MCP – lightweight Model Context Protocol server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python311
            python311Packages.poetry
            python311Packages.pip
            python311Packages.setuptools
            python311Packages.wheel
            # Add linters/test deps here if you want them in shell
            python311Packages.pytest
          ];

          shellHook = ''
            echo "🐍 Synesthetic MCP dev shell (Python 3.11 via Nix)"
            echo "Use 'poetry install' to create a .venv/"
            echo "Run tests with 'pytest'"
          '';
        };
      });
}
