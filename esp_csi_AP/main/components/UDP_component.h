#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"

#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include <lwip/netdb.h>

#include <list>

#define PORT 3333

typedef struct {
    struct sockaddr_in dest_addr;
    bool mode = 1;
} client_cfg;

static std::list<client_cfg> client_lst;
std::list<client_cfg>::iterator it;

const char *UDP_TAG = "UDP_Client";
static char payload[2048];
static bool HasCSI2Send = false;
static bool check_mode;

static void udp_server_task(void *pvParameters)
{
    char rx_buffer[128];
    while (true) {
        int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
        if (sock < 0) {
            ESP_LOGE(UDP_TAG, "Unable to create socket: errno %d", errno);
            break;
        }
        ESP_LOGI(UDP_TAG, "Socket created");

        struct sockaddr_in server_addr;
        server_addr.sin_addr.s_addr = inet_addr("192.168.4.1");
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(PORT);
        int rc  = bind(sock, (struct sockaddr*)&server_addr, sizeof(server_addr));
        if (rc < 0) {
            ESP_LOGE(UDP_TAG, "bind: %d %s", rc, strerror(errno));
            continue;
        }

        while (true) {
            if (HasCSI2Send) {
                int err = 0;
                for (it=client_lst.begin(); it!=client_lst.end(); it++) {
                    if ((*it).mode==1) {
                        err = sendto(sock, payload, strlen(payload), 0, (struct sockaddr*)&((*it).dest_addr), sizeof((*it).dest_addr));
                    }
                }
                HasCSI2Send = false;
                memset(payload, 0, sizeof(payload));
                if (err < 0) {
                    ESP_LOGE(UDP_TAG, "Error occurred during sending: errno %d", errno);
                    break;
                }

                struct sockaddr_storage source_addr;
                socklen_t socklen = sizeof(source_addr);
                memset(rx_buffer, 0, sizeof(*rx_buffer));
                int len = recvfrom(sock, rx_buffer, sizeof(rx_buffer)-1, 0, (struct sockaddr *)&source_addr, &socklen);

                if (len < 0) {
                    ESP_LOGE(UDP_TAG, "recvfrom failed: errno %d", errno);
                    break;
                }
                else {
                    rx_buffer[len] = 0;
                    if (strncmp(rx_buffer, "OK: ", 4)==0) {
                        ESP_LOGI(UDP_TAG, "Received expected message, reconnecting");
                        break;
                    }
                    if (check_mode==true) {
                        struct sockaddr_in *sa = (struct sockaddr_in *)&source_addr;
                        if (strcmp(inet_ntoa(sa->sin_addr.s_addr), inet_ntoa(client_lst.back().dest_addr.sin_addr.s_addr))==0) {
                            if (strcmp(rx_buffer, "rx")==0) {
                                printf("set rx\n");
                                client_lst.back().mode = 1;
                                check_mode = false;
                            }
                            else if (strcmp(rx_buffer, "tx")==0){
                                printf("set tx\n");
                                client_lst.back().mode = 0;
                                check_mode = false;
                            }
                        }
                    }
                    else {
                        //ESP_LOGI(UDP_TAG, "%s", rx_buffer);
                    }
                }
            }
            vTaskDelay(10);
        }

        if (sock!=-1) {
            ESP_LOGE(UDP_TAG, "Shutting down socket and restarting...");
            close(sock);
        }
    }
    vTaskDelete(NULL);
}