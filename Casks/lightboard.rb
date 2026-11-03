cask "lightboard" do
  version "0.1.3"
  sha256 "ee854c8e08951835ef487418a70e46bc9458dfe490cf73c329d2e40f1a7ea9cb"

  url "https://releases.viaduct.io/lightboard/#{version}/Lightboard-#{version}-universal.zip"
  name "Lightboard"
  desc "Control Philips Hue bridges directly over the local network"
  homepage "https://viaduct.io/"

  livecheck do
    url "https://releases.viaduct.io/lightboard/appcast.xml"
    strategy :sparkle, &:short_version
  end

  auto_updates true
  depends_on macos: :sequoia

  app "Lightboard.app"
end
