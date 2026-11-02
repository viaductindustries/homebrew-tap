cask "lightboard" do
  version "0.1.0"
  sha256 "eb641d8620f6c95ae0aeedba28512150bf3652a2457e14862a489138f0177717"

  url "https://releases.viaduct.io/lightboard/#{version}/Lightboard-#{version}-universal.zip"
  name "Lightboard"
  desc "Control Philips Hue bridges directly over the local network"
  homepage "https://viaduct.io/"

  auto_updates true
  depends_on macos: :sequoia

  app "Lightboard.app"
end
