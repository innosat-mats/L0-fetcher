RCLONE_VERSION = v1.60.0

build:
	mkdir -p build/layer-arm64/bin/ dist/
	wget -P build/ https://github.com/rclone/rclone/releases/download/$(RCLONE_VERSION)/rclone-$(RCLONE_VERSION)-linux-arm64.zip
	unzip -j build/rclone-$(RCLONE_VERSION)-linux-arm64.zip rclone-$(RCLONE_VERSION)-linux-arm64/rclone -d build/layer-arm64/bin/
	cd build/layer-arm64/ && zip -r ../../dist/layer-arm64.zip *

clean:
	rm -rv build dist
