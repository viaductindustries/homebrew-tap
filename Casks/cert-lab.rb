cask "cert-lab" do
  version "1.0.3"
  sha256 "f227ff5066d81a0bc3a078126c2660d3889e1601a7218be33eef77c8858ea3c3"

  url "https://github.com/viaductindustries/cert-lab/releases/download/v#{version}/Cert-Lab-#{version}-universal.zip"
  name "Cert Lab"
  desc "Private certificate authorities backed by 1Password"
  homepage "https://github.com/viaductindustries/cert-lab"

  depends_on macos: ">= :sonoma"

  app "Cert Lab.app"

  caveats <<~EOS
    Requires the 1Password desktop app and 1Password CLI.
    Enable Settings > Developer > Integrate with 1Password CLI in 1Password.
  EOS
end
