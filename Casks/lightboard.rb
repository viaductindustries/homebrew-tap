cask "lightboard" do
  version "0.1.2"
  sha256 "7faec84016758b5d0588f51c24230875f041623c23dcdaf2e363a1a7e8af08ec"

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
