PUBLIC_ADDRESS = pirxru@pirx.ru:obraz/public_html

default: build

build:
	obraz build

publish:
	rsync -avz --delete _site/ $(PUBLIC_ADDRESS)

clean:
	rm -fr _site

