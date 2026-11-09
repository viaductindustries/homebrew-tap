cask "lightboard" do
  version "0.1.5"
  sha256 "aeeec8780382386f8dce097f1ec9dc2239f430b32d8b66b2e0a2b715735f6908"

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
