.PHONY: build test run clean package

build:
	cd scanner && cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j
	cd frontend && npm ci && npm run build

test:
	cd scanner/build && ctest --output-on-failure
	cd webapp && python -m pytest
	cd frontend && npm test -- --run

run:
	cd webapp && DISKVIZ_READ_TOKEN=dev-read DISKVIZ_WRITE_TOKEN=dev-write uvicorn diskviz_api.main:app --host 127.0.0.1 --port 8765 --reload

clean:
	rm -rf scanner/build frontend/node_modules frontend/dist webapp/diskviz_api/static

package:
	./scripts/package.sh
