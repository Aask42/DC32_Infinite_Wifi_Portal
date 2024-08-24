import uos
import gc
import micropython as mp
import urequests
import uasyncio as asyncio
from CONFIG.OTA_CONFIG import OTA_HOST, PROJECT_NAME, FILENAMES
from CONFIG.MQTT_CONFIG import MQTT_CLIENT_ID

class OTAUpdater:
    def __init__(self, msg_string: str):
        self.msg_string = msg_string
    
    async def update_file_replace(self):
        """
        Updates a file from an OTA server.
        
        This method fetches the file content from the OTA server and replaces
        the local file with the new content.

        :raises Exception: If there's an error during the update process.
        """
        print(f"Starting update process for {self.msg_string}...")
        filename = self.msg_string
        
        mp.mem_info(1)
        gc.collect()
        
        try:
            updated = False
            print(f"Updating file {filename}")
            
            for item in FILENAMES:
                print(f"Checking if {filename} is in {item}")

                if filename in item:
                    file_to_write = item
                    print(f"Found filename! Simple name: {filename} Fully Qualified: {item}")

                    # Define the temporary file name in the same directory
                    tmp_filename = f'{file_to_write}.tmp'
                    
                    # Fetch the new content
                    response_text = await self._http_get(f'{OTA_HOST}/ota_updates/{MQTT_CLIENT_ID}/{filename}')
                    print(f"Response text received: {response_text}")

                    # Write the new content to a temporary file
                    try:
                        with open(tmp_filename, 'w') as source_file:
                            source_file.write(response_text)
                        print(f"Content written to {tmp_filename}")
                    except Exception as e:
                        print(f"Exception writing to temp file: {e}")
                        continue

                    # Remove the original file if it exists
                    try:
                        if filename in uos.listdir('/CONFIG'):
                            uos.remove(file_to_write)
                            print(f"Removed old file: {file_to_write}")
                    except Exception as e:
                        print(f"Exception removing old file: {e}")

                    # Rename the temporary file to the original file name
                    try:
                        uos.rename(tmp_filename, file_to_write)
                        print(f"Renamed {tmp_filename} to {file_to_write}")
                    except Exception as e:
                        print(f"Exception renaming temp file: {e}")

                    break

        except Exception as e:
            print(f"Exception during update process: {e}")

    async def _http_get(self, url: str) -> str:
        """
        Perform a non-blocking HTTP GET request to the specified URL.

        :param url: The URL to fetch.
        :return: The response text.
        """
        try:
            response = urequests.get(url)
            response_text = response.text
            response.close()
            return response_text
        except Exception as e:
            print(f"Exception during HTTP GET: {e}")
            return ""

# Example usage:
# updater = OTAUpdater("MQTT_CONFIG.py")
# asyncio.run(updater.update_file_replace())

