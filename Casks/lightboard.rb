cask "lightboard" do
  version "0.1.6"
  sha256 "ca833eaee01871daf288c569cfad191e24a1e3dc080731293c0e9aad5bb1389a"

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
