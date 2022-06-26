#include "math.h"
#include <sstream>
#include <iostream>

#include "UDP_component.h"

typedef struct {
    char mac[20] = {0};
    double timestamp;
    signed char *CSI_data_ptr;
} CSI_info;

SemaphoreHandle_t mutex = xSemaphoreCreateMutex();
static bool socket_created = false;

void _wifi_csi_cb(void *ctx, wifi_csi_info_t *data) {
    xSemaphoreTake(mutex, portMAX_DELAY);
    std::stringstream ss;

    //arrange CSI data
    CSI_info Ci;
    wifi_csi_info_t d = data[0];
    sprintf(Ci.mac, "%02X:%02X:%02X:%02X:%02X:%02X", d.mac[0], d.mac[1], d.mac[2], d.mac[3], d.mac[4], d.mac[5]);
    Ci.timestamp = (double)(d.rx_ctrl.timestamp/1000000.0);
    Ci.CSI_data_ptr = (signed char*)((*data).buf);

    ss << "{\n\"client_MAC\": \""
       << Ci.mac << "\", \n"
       << "\"recieved_time\": "
       << Ci.timestamp << ", \n";
    int data_len;
    if (CONFIG_SHOULD_COLLECT_ONLY_LLTF) {
        data_len = 128;
    }
    else {
        data_len = data->len;
    }
    ss << "\"CSI_info\": [";
    //calculate amplitute & phase with real & imag part
    //per subcarrier occupies 2 indexes (real & imag)
    for (int i=0; i<data_len; i+=2) {
        ss << "[" << (int)sqrt(pow(Ci.CSI_data_ptr[i*2], 2)+pow(Ci.CSI_data_ptr[(i*2)+1], 2)) << ", "
        << (int)atan2(Ci.CSI_data_ptr[i*2], Ci.CSI_data_ptr[(i*2)+1]) << "], ";
    }
    ss.seekp(-2, ss.cur);
    ss << "]\n}";
    strcpy(payload, ss.str().c_str());
    HasCSI2Send = true;

    fflush(stdout);
    vTaskDelay(0);
    xSemaphoreGive(mutex);
}

void dhcps_cb(u8_t client_ip[4])
{
    printf("DHCP server assigned IP to a station, IP is: %d.%d.%d.%d\n", client_ip[0], client_ip[1], client_ip[2], client_ip[3]);

    ip_event_ap_staipassigned_t evt;
    memset(&evt, 0, sizeof(ip_event_ap_staipassigned_t));
    memcpy((char *)&evt.ip.addr, (char *)client_ip, sizeof(evt.ip.addr));
    int ret = esp_event_send_internal(IP_EVENT, IP_EVENT_AP_STAIPASSIGNED, &evt, sizeof(evt), 0);
    if (ESP_OK != ret) {
        printf("dhcps cb: failed to post IP_EVENT_AP_STAIPASSIGNED (%d)", ret);
        
    }
    char ip[20] = {0};
    sprintf(ip, "%d.%d.%d.%d", client_ip[0], client_ip[1], client_ip[2], client_ip[3]);
    if (client_lst.size()==0) {
            client_cfg cfg;
            cfg.dest_addr.sin_addr.s_addr = inet_addr(ip);
            cfg.dest_addr.sin_family = AF_INET;
            cfg.dest_addr.sin_port = htons(PORT);
            client_lst.push_back(cfg);
            printf("client count: %d\n", client_lst.size());
            check_mode = true;
    }
    else {
        for (it=client_lst.begin(); it!=client_lst.end(); it++) {
            if (strcmp(inet_ntoa((*it).dest_addr.sin_addr.s_addr), ip)!=0) {
                client_cfg cfg;
                cfg.dest_addr.sin_addr.s_addr = inet_addr(ip);
                cfg.dest_addr.sin_family = AF_INET;
                cfg.dest_addr.sin_port = htons(PORT);
                client_lst.push_back(cfg);
                printf("client count: %d\n", client_lst.size());
                check_mode = true;
                break;
            }
        }
    }
    if (socket_created!=true) {
        xTaskCreate(udp_server_task, "udp_server", 10240, NULL, 5, NULL);
        socket_created = true;
    }
}

void csi_init() {
    ESP_ERROR_CHECK(esp_wifi_set_csi(1));
    wifi_csi_config_t configuration_csi;
    configuration_csi.lltf_en = 1;
    configuration_csi.htltf_en = 1;
    configuration_csi.stbc_htltf2_en = 1;
    configuration_csi.ltf_merge_en = 1;
    configuration_csi.channel_filter_en = 0;
    configuration_csi.manu_scale = 0;
    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&configuration_csi));

    //register cb
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(&_wifi_csi_cb, NULL));
    dhcps_set_new_lease_cb(dhcps_cb);
}