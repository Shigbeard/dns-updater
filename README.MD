# DNS-Updater

This is a simple script to automatically update DNS A Records for a given domain. It's intended to run under docker, but can be run as a standalone script.

I wrote this in a couple hours because I was angry with my ISP changing my IP address yet again. As my upstream provider is Vultr, this script comes pre-packaged to work with Vultr. Because I haven't figured out how to make the DNS handler modular, you'll have to modify the script to work with your provider. It's prety simple.

This script consists of 2 core components: Firstly, every 30 seconds, a request is made to a website that will return the IP address of the requester. The second component comes into if the IP address returned changes, when the script updates the DNS records for the given domain.

## Usage

### Docker

Modify the docker-compose file to include your api key. Modify `app/config.json` to include your specific domain, and dns records you'd like updated. Then run `docker-compose up -d` to start the container.

### Standalone

Run `pip install -r app/requirements.txt` to install dependencies. Modify `app/config.json` to include your specific domain, and dns records you'd like updated. Set an environment variable with your api key (e.g. `export API_KEY=1234567890`). Run `python app/app.py` to run the script.

## Tweaking for your own upstream provider

In `app/app.py` there's a section of code [here](app/app.py#L6-L28) that handles interaction with the Upstream DNS provider. You'll need to modify this to work with your provider. It's mostly just a matter of changing the API endpoint. But sometimes you'll need to adjust the way the data is read/written. For example, Vultr expects a patch request to be made to update a record, with the new IP address being in the 'data' field. Whereas Cloudflare expects a put request to be made, with the new IP address being in the 'content' field. Consult your provider's API documentation to figure out what you need to do.

You might even need to tweak the rest of the code.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details