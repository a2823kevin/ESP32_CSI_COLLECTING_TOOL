#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_spi_flash.h"
#include "freertos/event_groups.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_http_client.h"
#include "esp_log.h"
#include "nvs_flash.h"

#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include <lwip/netdb.h>

#include "components/nvs_component.h"

/*
 * The examples use WiFi configuration that you can set via 'idf.py menuconfig'.
 *
 * If you'd rather not, just change the below entries to strings with
 * the config you want - ie #define ESP_WIFI_SSID "mywifissid"
 */
#define ESP_WIFI_SSID      CONFIG_ESP_WIFI_SSID
#define ESP_WIFI_PASS      CONFIG_ESP_WIFI_PASSWORD

#ifdef CONFIG_WIFI_CHANNEL
#define WIFI_CHANNEL CONFIG_WIFI_CHANNEL
#else
#define WIFI_CHANNEL 6
#endif

#define PORT 3333

static EventGroupHandle_t s_wifi_event_group;
static char server_ip[20] = {0};
static const char *TAG = "Active CSI collection (STA)";
static const char *UDP_TAG = "UDP_Client";
static int init_counter = 0;
static bool socket_created = false;

static void udp_server_task(void *pvParameters) {
    struct sockaddr_in* dest_addr;

    int addr_family = AF_INET;
    int ip_protocol = IPPROTO_IP;

    while (true) {
        int sock = socket(addr_family, SOCK_DGRAM, ip_protocol);
        if (sock < 0) {
            ESP_LOGE(UDP_TAG, "Unable to create socket: errno %d", errno);
            break;
        }
        ESP_LOGI(UDP_TAG, "Socket created");

        struct sockaddr_in server_addr;
        server_addr.sin_addr.s_addr = inet_addr(server_ip);
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(PORT);
        int rc  = bind(sock, (struct sockaddr*)&server_addr, sizeof(server_addr));
        if (rc < 0) {
            ESP_LOGE(UDP_TAG, "bind: %d %s", rc, strerror(errno));
            continue;
        }
        struct sockaddr_in dest_addr;
        dest_addr.sin_addr.s_addr = inet_addr("192.168.4.1");
        dest_addr.sin_family = AF_INET;
        dest_addr.sin_port = htons(PORT);
        while (init_counter<500) {
            int err = sendto(sock, "tx", strlen("tx"), 0, (struct sockaddr *)&dest_addr, sizeof(dest_addr));
            init_counter++;
            vTaskDelay(10);
        }
        while (true) {
            int err = sendto(sock, "foo", strlen("foo"), 0, (struct sockaddr *)&dest_addr, sizeof(dest_addr));
            if (socket_created==false) {
                close(sock);
                vTaskDelete(NULL);
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

static void event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
    if (event_id==WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    }
    else if (event_id==WIFI_EVENT_STA_DISCONNECTED) {
        memset(server_ip, 0, sizeof(*server_ip));
        init_counter = 0;
        socket_created = false;
        ESP_LOGI(TAG, "Retry connecting to the AP");
        esp_wifi_connect();
    }
    else if (event_id==IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        sprintf(server_ip, IPSTR, IP2STR(&event->ip_info.ip));
        ESP_LOGI(TAG, "Got ip: %s", server_ip);
        if (socket_created==false) {
            xTaskCreate(udp_server_task, "udp_server", 20480, NULL, 5, NULL);
            socket_created = true;
        }
    }
}

void station_init() {
    s_wifi_event_group = xEventGroupCreate();

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &event_handler, NULL, NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &event_handler, NULL, NULL));

    wifi_sta_config_t wifi_sta_config = {};
    wifi_sta_config.channel = WIFI_CHANNEL;

    wifi_config_t wifi_config = {
            .sta = wifi_sta_config,
    };
    strlcpy((char *) wifi_config.sta.ssid, ESP_WIFI_SSID, sizeof(ESP_WIFI_SSID));
    strlcpy((char *) wifi_config.sta.password, ESP_WIFI_PASS, sizeof(ESP_WIFI_PASS));

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    esp_wifi_set_ps(WIFI_PS_NONE);

    ESP_LOGI(TAG, "connect to ap SSID: %s, password: %s", ESP_WIFI_SSID, ESP_WIFI_PASS);
}

extern "C" void app_main() {
    nvs_init();
    station_init();
}