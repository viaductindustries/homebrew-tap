cask "lightboard" do
  version "0.1.4"
  sha256 "76aa5cbb4588aabad480a1bd92afcb14631d8e657de908783089b3c691243d84"

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
