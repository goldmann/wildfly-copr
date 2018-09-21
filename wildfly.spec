%global namedreltag .Final
%global namedversion %{version}%{?namedreltag}

%global cachedir %{_var}/cache/%{name}
%global libdir %{_var}/lib/%{name}
%global rundir %{_var}/run/%{name}
%global homedir %{_datadir}/%{name}
%global bindir %{homedir}/bin
%global logdir %{_var}/log/%{name}
%global confdir %{_sysconfdir}/%{name}

%global __jar_repack 0
%global _binaries_in_noarch_packages_terminate_build   0

%global wfuid 185

Name:             wildfly
Version:          14.0.1
Release:          1%{?dist}
Summary:          WildFly Application Server
License:          LGPLv2+ and ASL 2.0 and GPLv2 with exceptions
URL:              http://wildfly.org/

Source0:          http://download.jboss.org/wildfly/%{namedversion}/wildfly-%{namedversion}.tar.gz

# Makes possible to run WildFly AS in different directory by creating the structure and copying required configuration files
Source1:          wildfly-cp.sh

# The WildFly systemd service
Source2:          wildfly.service

# The WildFly systemd configuration file
Source3:          wildfly.conf

# A simple launch script
Source4:          launch.sh

Provides:         jboss-as = %{version}-%{release}
Obsoletes:        jboss-as < 7.1.1-22

BuildArch:        noarch

# Required for compiling JSP for example
Requires:         java-devel >= 1:1.8

Requires(pre):    shadow-utils
Requires(post):   systemd-units
Requires(preun):  systemd-units
Requires(postun): systemd-units

BuildRequires:    systemd-units

# To not collide with the version shipped in Fedora
Epoch:            1

%description
WildFly Application Server (formerly known as JBoss Application Server) is the
latest release in a series of WildFly offerings. WildFly Application Server, is
a fast, powerful, implementation of the Java Enterprise Edition 6
specification.  The state-of-the-art architecture built on the Modular Service
Container enables services on-demand when your application requires them.

%package doc
Summary:          Documentation for %{name}
Group:            Documentation

%description doc
This package contains the documentation for %{name}.

%prep
%setup -q -n wildfly-%{namedversion}

%install

install -d -m 755 $RPM_BUILD_ROOT%{_javadir}/%{name}
install -d -m 755 $RPM_BUILD_ROOT%{homedir}
install -d -m 755 $RPM_BUILD_ROOT%{confdir}
install -d -m 755 $RPM_BUILD_ROOT%{rundir}
install -d -m 770 $RPM_BUILD_ROOT%{cachedir}/auth
install -d -m 755 $RPM_BUILD_ROOT%{_unitdir}
install -d -m 755 $RPM_BUILD_ROOT%{_bindir}
install -d -m 755 $RPM_BUILD_ROOT%{_docdir}/%{name}

for mode in standalone domain; do
  install -d -m 755 $RPM_BUILD_ROOT%{homedir}/${mode}
  install -d -m 775 $RPM_BUILD_ROOT%{libdir}/${mode}/data
  install -d -m 755 $RPM_BUILD_ROOT%{cachedir}/${mode}
  install -d -m 775 $RPM_BUILD_ROOT%{logdir}/${mode}
done

install -d -m 775 $RPM_BUILD_ROOT%{libdir}/domain/servers

pushd .
  # We don't need Windows files
  find bin/ -type f -name "*.bat" -delete
  find bin/ -type f -name "*.exe" -delete

  # Install systemd files
  install -m 644 %{SOURCE2} $RPM_BUILD_ROOT%{_unitdir}/%{name}.service
  install -m 644 %{SOURCE3} $RPM_BUILD_ROOT%{confdir}/%{name}.conf

  # We don't need legacy init scripts
  rm -rf bin/init.d

  # Prepare directory for properties files
  install -d -m 755 docs/examples/properties

  # Copy logging.properties and mgmt-users.properties so we can reuse it later in wildfly-cp script
  cp standalone/configuration/logging.properties docs/examples/properties/
  cp standalone/configuration/mgmt-users.properties docs/examples/properties/
  # Lower a bit the permissions, so ordinary user can copy it. It's an example file!
  chmod 644 docs/examples/properties/mgmt-users.properties

  # standalone
  mv standalone/configuration $RPM_BUILD_ROOT%{confdir}/standalone
  mv standalone/deployments $RPM_BUILD_ROOT%{libdir}/standalone/deployments
  mv standalone/lib $RPM_BUILD_ROOT%{libdir}/standalone/lib
  mv standalone/tmp $RPM_BUILD_ROOT%{cachedir}/standalone/tmp

  # domain
  mv domain/configuration $RPM_BUILD_ROOT%{confdir}/domain
  mv domain/tmp $RPM_BUILD_ROOT%{cachedir}/domain/tmp

  # appclient
  mv appclient/configuration $RPM_BUILD_ROOT%{confdir}/appclient

  mv bin/jboss-cli.xml $RPM_BUILD_ROOT%{confdir}
  mv docs/* $RPM_BUILD_ROOT%{_docdir}/%{name}
  mv jboss-modules.jar copyright.txt README.txt LICENSE.txt welcome-content docs bin appclient modules $RPM_BUILD_ROOT%{homedir}

  # Install the launch script
  install -m 755 %{SOURCE4} $RPM_BUILD_ROOT%{bindir}/launch.sh
popd

chmod 775 $RPM_BUILD_ROOT%{libdir}/standalone/deployments

pushd $RPM_BUILD_ROOT%{homedir}

  # Standalone
  ln -s %{confdir}/standalone standalone/configuration
  ln -s %{libdir}/standalone/deployments standalone/deployments
  ln -s %{libdir}/standalone/data standalone/data
  ln -s %{libdir}/standalone/lib standalone/lib
  ln -s %{logdir}/standalone standalone/log
  ln -s %{cachedir}/standalone/tmp standalone/tmp

  # Domain
  ln -s %{confdir}/domain domain/configuration
  ln -s %{libdir}/domain/data domain/data
  ln -s %{libdir}/domain/servers domain/servers
  ln -s %{logdir}/domain domain/log
  ln -s %{cachedir}/domain/tmp domain/tmp

  ln -s %{confdir}/appclient appclient

  # Auth dir
  ln -s %{cachedir}/auth auth
popd


pushd $RPM_BUILD_ROOT%{_bindir}
  # jboss-cli
  ln -s %{bindir}/jboss-cli.sh jboss-cli

  install -m 755 %{SOURCE1} %{name}-cp
popd

%pre
# Add wildfly user and group
getent group %{name} >/dev/null || groupadd -f -g %{wfuid} -r %{name}
if ! getent passwd %{name} >/dev/null ; then
  if ! getent passwd %{wfuid} >/dev/null ; then
    useradd -r -u %{wfuid} -g %{name} -d %{homedir} -s /sbin/nologin -c "The WildFly Application Server user" %{name}
  else
    useradd -r -g %{name} -d %{homedir} -s /sbin/nologin -c "The WildFly Application Server user" %{name}
  fi
fi
exit 0

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%{homedir}/appclient
%dir %{bindir}
%{bindir}/*.conf
%{bindir}/*.sh
%{bindir}/*.properties
%{bindir}/*.ps1
%{bindir}/.jbossclirc
%{bindir}/*.jar
%{bindir}/client
%{_bindir}/*
%dir %{homedir}
%{homedir}/auth
%{homedir}/domain
%{homedir}/standalone
%{homedir}/modules
%{homedir}/welcome-content
%{homedir}/jboss-modules.jar
%attr(-,root,wildfly) %dir %{libdir}
%attr(-,root,wildfly) %{libdir}/standalone
%attr(-,root,wildfly) %{libdir}/domain
%attr(0775,root,wildfly) %dir %{rundir}
%attr(0775,root,wildfly) %dir %{cachedir}
%attr(0775,root,wildfly) %dir %{cachedir}/standalone
%attr(0775,root,wildfly) %dir %{cachedir}/standalone/tmp
%attr(0775,root,wildfly) %dir %{cachedir}/domain
%attr(0775,root,wildfly) %dir %{cachedir}/domain/tmp
%attr(0770,root,wildfly) %dir %{logdir}
%attr(0770,root,wildfly) %dir %{logdir}/standalone
%attr(0770,root,wildfly) %dir %{logdir}/domain
%attr(0775,root,wildfly) %dir %{confdir}
%attr(0775,root,wildfly) %dir %{confdir}/appclient
%attr(0775,root,wildfly) %dir %{confdir}/standalone
%attr(0775,root,wildfly) %dir %{confdir}/domain
%attr(0700,wildfly,wildfly) %dir %{cachedir}/auth
%attr(0600,wildfly,wildfly) %config(noreplace) %{confdir}/appclient/*.properties
%attr(0664,wildfly,wildfly) %config(noreplace) %{confdir}/appclient/*.xml
%attr(0600,wildfly,wildfly) %config(noreplace) %{confdir}/standalone/*.properties
%attr(0664,wildfly,wildfly) %config(noreplace) %{confdir}/standalone/*.xml
%attr(0600,wildfly,wildfly) %config(noreplace) %{confdir}/domain/*.properties
%attr(0664,wildfly,wildfly) %config(noreplace) %{confdir}/domain/*.xml
%config(noreplace) %{confdir}/%{name}.conf
%config(noreplace) %{confdir}/jboss-cli.xml
%{_unitdir}/%{name}.service
%doc %{homedir}/README.txt
%doc %{homedir}/copyright.txt
%doc %{homedir}/LICENSE.txt
%dir %{_javadir}/%{name}

%files doc
%{_docdir}/%{name}

%changelog
* Sun Sep 23 2018 Ricardo Arguello - 1:14.0.1-1
- Upstream 14.0.1.Final release

* Wed Oct 25 2017 Ricardo Arguello - 1:11.0.0-1
- Upstream 11.0.0.Final release

* Mon Jul 10 2017 Ricardo Arguello - 1:10.1.0-1
- Upstream 10.1.0.Final release

* Wed Feb 24 2016 Marek Goldmann - 1:10.0.0-1
- Upstream 10.0.0.Final release

* Fri Aug 07 2015 Marek Goldmann - 1:9.0.1-2
- Missed systemd-units BR

* Fri Aug 07 2015 Marek Goldmann - 1:9.0.1-1
- Initial packaging of the all-in-one distribution
