FROM grafana/grafana:main-ubuntu

COPY provisioning/* /etc/grafana/setup
COPY entrypoint.sh /entrypoint.sh

USER root
RUN chmod +x /entrypoint.sh

USER grafana
ENTRYPOINT ["/entrypoint.sh"]