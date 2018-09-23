#!/bin/sh

usage()
{
cat << EOF
usage: $0 options

Makes possible to run WildFly AS in different directory by creating the structure and copying required configuration files.

OPTIONS:
   -h      Show this message
   -c      WildFly configuration xml file (see \$JBOSS_HOME/docs/examples/configs/), default: standalone-web.xml
   -l      Location where the directory structure should be created (required)
   -p      Port offset, see https://community.jboss.org/docs/DOC-16705
EOF
}

STANDALONE_XML="standalone.xml"

while getopts “hc:l:p:” OPTION
do
    case $OPTION in
        h)
            usage
            exit 1
            ;;
        c)
            STANDALONE_XML=$OPTARG
            ;;
        l)
            LOCATION=$OPTARG
            ;;
        p)
            PORT_OFFSET=$OPTARG
            ;;
        ?)
            usage
            exit
            ;;
    esac
done

if [[ -z $LOCATION ]]
then
    usage
    exit 1
fi

if [ "x$JBOSS_HOME" = "x" ]; then
    JBOSS_HOME="/usr/share/wildfly"
fi

mkdir -p ${LOCATION}/{bin,data,deployments,log,tmp,configuration}

cp $JBOSS_HOME/docs/examples/configs/$STANDALONE_XML ${LOCATION}/configuration/
cp $JBOSS_HOME/docs/examples/properties/logging.properties ${LOCATION}/configuration/
cp $JBOSS_HOME/docs/examples/properties/mgmt-users.properties ${LOCATION}/configuration/

# Create the standalone script
echo "#!/bin/sh

JBOSS_BASE_DIR=${LOCATION} ${JBOSS_HOME}/bin/standalone.sh -c ${STANDALONE_XML}" > ${LOCATION}/bin/standalone.sh

# Make sure the mgmt-users.properties file has correct permissions!
chmod 600 ${LOCATION}/configuration/mgmt-users.properties

# Set the executable permissions correctly
chmod 755 ${LOCATION}/bin/standalone.sh

# Set the port offset (if specified)
if [ "x$PORT_OFFSET" != "x" ]; then
  sed -i s/'\(socket-binding-group name="standard-sockets" default-interface="public"\).*'/"\1 port-offset=\"${PORT_OFFSET}\">"/ ${LOCATION}/configuration/${STANDALONE_XML}
fi

echo -e "Directory ${LOCATION} is prepared to launch WildFly AS!\n\nYou can now boot your instance: ${LOCATION}/bin/standalone.sh"
