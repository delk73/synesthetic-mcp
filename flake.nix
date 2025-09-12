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
        py = pkgs.python311;
        pyPkgs = pkgs.python311Packages;
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            py
            poetry
            pyPkgs.pip
            pyPkgs.setuptools
            pyPkgs.wheel
            pyPkgs.pytest
          ];

          shellHook = ''
            echo "🐍 Synesthetic MCP dev shell"
            echo "Python: ${py.version}"
            echo "Use 'poetry install' to set up a .venv/"
            echo "Run tests with 'pytest'"
          '';
        };
      });
}
