cask "cert-lab" do
  version "1.0.4"
  sha256 "d48900d588635da6d2c1fcc1765eef366db97af1ec364e53e5298a50878baa67"

  url "https://github.com/viaductindustries/cert-lab/releases/download/v#{version}/Cert-Lab-#{version}-universal.zip"
  name "Cert Lab"
  desc "Private certificate authorities backed by 1Password"
  homepage "https://github.com/viaductindustries/cert-lab"

  depends_on macos: :sonoma

  app "Cert Lab.app"

  caveats <<~EOS
    Requires the 1Password desktop app and 1Password CLI.
    Enable Settings > Developer > Integrate with 1Password CLI in 1Password.
  EOS
end
