// Copyright 2026 Juan Carlos Nevarez. Apache-2.0; see repository LICENSE.
// Native Fast DDS 2.14 probe: report the middleware authentication callback.
#include <fastdds/dds/domain/DomainParticipantFactory.hpp>
#include <fastdds/dds/domain/DomainParticipantListener.hpp>
#include <fastdds/dds/domain/qos/DomainParticipantQos.hpp>
#include <fastdds/rtps/participant/ParticipantDiscoveryInfo.h>
#include <fastdds/rtps/transport/UDPv4TransportDescriptor.h>
#include <fastrtps/utils/IPLocator.h>
#include <atomic>
#include <chrono>
#include <iostream>
#include <memory>
#include <string>
#include <thread>

using namespace eprosima::fastdds::dds;
namespace rtps = eprosima::fastrtps::rtps;

class AuthenticationObserver : public DomainParticipantListener {
public:
    std::atomic<int> accepted{0};
    std::atomic<int> rejected{0};
    void onParticipantAuthentication(DomainParticipant*, rtps::ParticipantAuthenticationInfo&& info) override {
        if (info.status == rtps::ParticipantAuthenticationInfo::AUTHORIZED_PARTICIPANT) {
            ++accepted;
            std::cout << "AUTHENTICATION_ACCEPTED" << std::endl;
        } else {
            ++rejected;
            std::cout << "AUTHENTICATION_REJECTED" << std::endl;
        }
    }
};

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "Usage: authentication_probe /absolute/enclave/directory" << std::endl;
        return 2;
    }
    DomainParticipantQos qos;
    qos.name("security_lab_authentication_observer");
    auto& properties = qos.properties().properties();
    properties.emplace_back("dds.sec.auth.plugin", "builtin.PKI-DH");
    properties.emplace_back("dds.sec.access.plugin", "builtin.Access-Permissions");
    properties.emplace_back("dds.sec.crypto.plugin", "builtin.AES-GCM-GMAC");
    const std::string base = std::string("file://") + argv[1] + "/";
    properties.emplace_back("dds.sec.auth.builtin.PKI-DH.identity_ca", base + "identity_ca.cert.pem");
    properties.emplace_back("dds.sec.auth.builtin.PKI-DH.identity_certificate", base + "cert.pem");
    properties.emplace_back("dds.sec.auth.builtin.PKI-DH.private_key", base + "key.pem");
    properties.emplace_back("dds.sec.access.builtin.Access-Permissions.permissions_ca", base + "permissions_ca.cert.pem");
    properties.emplace_back("dds.sec.access.builtin.Access-Permissions.governance", base + "governance.p7s");
    properties.emplace_back("dds.sec.access.builtin.Access-Permissions.permissions", base + "permissions.p7s");
    auto udp = std::make_shared<eprosima::fastdds::rtps::UDPv4TransportDescriptor>();
    udp->interfaceWhiteList.push_back("127.0.0.1");
    qos.transport().use_builtin_transports = false;
    qos.transport().user_transports.push_back(udp);
    rtps::Locator_t peer;
    rtps::IPLocator::setIPv4(peer, "127.0.0.1");
    peer.port = 0;
    qos.wire_protocol().builtin.initialPeersList.push_back(peer);
    AuthenticationObserver observer;
    auto factory = DomainParticipantFactory::get_instance();
    auto participant = factory->create_participant(42, qos, &observer);
    if (!participant) {
        std::cerr << "PROBE_INITIALIZATION_FAILED" << std::endl;
        return 3;
    }
    std::cout << "PROBE_READY" << std::endl;
    std::this_thread::sleep_for(std::chrono::seconds(8));
    factory->delete_participant(participant);
    std::cout << "{\"accepted\":" << observer.accepted << ",\"rejected\":" << observer.rejected << "}" << std::endl;
    return 0;
}
