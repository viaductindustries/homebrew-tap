cask "squeak" do
  version "0.1.0"
  sha256 "69ee4299c9092bd931097b6d4728bedd75704c7fe0079599977781a1c7316987"

  url "https://github.com/viaductindustries/squeak/releases/download/v#{version}/Squeak-#{version}-universal.zip"
  name "Squeak"
  desc "Menu bar app that decides what extra mouse buttons do"
  homepage "https://github.com/viaductindustries/squeak"

  depends_on macos: :sequoia

  app "Squeak.app"

  uninstall quit: "io.viaduct.squeak"

  zap trash: "~/Library/Preferences/io.viaduct.squeak.plist"

  caveats <<~EOS
    Squeak needs Accessibility access to see mouse buttons.
    Allow it in System Settings > Privacy & Security > Accessibility.
  EOS
end
