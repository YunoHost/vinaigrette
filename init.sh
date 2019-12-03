
apt-get install nginx pbuilder reprepro rebuildd gawk sendxmpp -y
apt-get install qemu-system-arm debootstrap cdebootstrap qemu-user-static -y
apt-get install python-virtualenv python3-pip -y
apt-get install boxes -y

# Fix the damn pbuilder-satistydepends (aptitude causes segfault on ARM)
cd /usr/lib/pbuilder
rm pbuilder-satisfydepends
ln -s pbuilder-satisfydepends-apt pbuilder-satisfydepends

VINAIGRETTE_HOME="/home/vinaigrette"

cd $VINAIGRETTE_HOME
source config/config

ln -s /root/keys config/keys
gpg --import config/keys/$DEBSIGN_KEYID.key
gpg --import config/keys/$DEBSIGN_KEYID.pub

mkdir gitrepos
cd gitrepos/
git clone https://github.com/yunohost/yunohost
git clone https://github.com/yunohost/yunohost-admin
git clone https://github.com/yunohost/ssowat SSOwat
git clone https://github.com/yunohost/moulinette
git clone https://github.com/yunohost/metronome
git clone https://github.com/YunoHost/rspamd
git clone https://git.donarmstrong.com/unscd.git

cd yunohost
git checkout buster  && git symbolic-ref refs/heads/buster-unstable refs/heads/buster
cd ..

mkdir -p /var/www/repo/debian/conf/
ln -s $VINAIGRETTE_HOME/config/distributions /var/www/repo/debian/conf/distributions

rm /etc/rebuildd/rebuilddrc
ln -s $VINAIGRETTE_HOME/config/rebuildd.conf /etc/rebuildd/rebuilddrc
rm /etc/default/rebuildd
ln -s $VINAIGRETTE_HOME/config/rebuildd.default /etc/default/rebuildd

ln -s $VINAIGRETTE_HOME/images /var/cache/pbuilder/images
ln -s /var/cache/pbuilder/result $PBUILDER_RESULTS

rm -f /etc/pbuilderrc
ln -s $PBUILDER_CONF/pbuilder.conf /etc/pbuilderrc

cp $VINAIGRETTE_HOME/config/nginx.conf /etc/nginx/sites-enabled/repo.conf

cat $VINAIGRETTE_HOME/config/keys/$DEBSIGN_KEYID.pub | apt-key add
cat $VINAIGRETTE_HOME/config/sources.list > /etc/apt/sources.list.d/vinaigrette.list

sed -i "s/__REPO_URL__/$REPO_URL/g" /etc/nginx/sites-enabled/repo.conf
sed -i "s/__REPO_URL__/$REPO_URL/g" /etc/apt/sources.list.d/vinaigrette.list
echo "deb https://deb.nodesource.com/node_4.x buster main" >> /etc/apt/sources.list

echo "127.0.0.1 $REPO_URL" >> /etc/hosts
service nginx reload

rebuildd init
