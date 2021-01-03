with builtins; 
import (fetchTarball {
  name   = "pin-nixpkgs";
  url    = "https://github.com/nixos/nixpkgs/archive/f71e439688e4c4b231e0f419f81df6610fdaa231.tar.gz";
  sha256 = "0ri8smcvi6xbr369xd466i21x358gcggsz4nlphqzjnx1in8c3lx";
}) { config = {}; overlays = []; }
