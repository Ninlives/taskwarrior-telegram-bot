{ pkgs ? import ./pkgs.nix }:
let
  inherit (pkgs.python3Packages)
    buildPythonApplication tasklib python-telegram-bot APScheduler setuptools
    pytest fetchPypi;
  inherit (pkgs.lib) sourceFilesBySuffices;
  fixed-bot = python-telegram-bot.overridePythonAttrs (a: {
    src = fetchPypi {
      pname = "python-telegram-bot";
      version = "13.1";
      sha256 = "10l23j46b5sh26qqs0dmjhwxh8bakwmkf1acxcfbgmq8xl4bpvjz";
    };
    propagatedBuildInputs = a.propagatedBuildInputs or [ ] ++ [ APScheduler ];
  });
  fixed-lib = tasklib.overridePythonAttrs (a: {
    checkInputs = a.checkInputs or [ ] ++ [ pytest ];
    checkPhase = ''
      pytest tasklib/tests.py -k 'not test_complex_eoy_conversion and not test_simple_eoy_conversion'
    '';
  });
in buildPythonApplication {
  pname = "taskwarrior-telegram-bot";
  version = "0.1.0";

  src = sourceFilesBySuffices ./. [ ".py" ];
  propagatedBuildInputs = [ fixed-bot setuptools fixed-lib ];
}
