RCLONE_VERSION = v1.60.1

build:
	mkdir -p build/layer-amd64/bin/ dist/
	wget -P build/ https://github.com/rclone/rclone/releases/download/$(RCLONE_VERSION)/rclone-$(RCLONE_VERSION)-linux-amd64.zip
	unzip -j build/rclone-$(RCLONE_VERSION)-linux-amd64.zip rclone-$(RCLONE_VERSION)-linux-amd64/rclone -d build/layer-amd64/bin/
	cd build/layer-amd64/ && zip -r ../../dist/layer-amd64.zip *

clean:
	rm -rv build dist
