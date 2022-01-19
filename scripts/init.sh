
apt-get install nginx sbuild schroot reprepro gawk sendxmpp -y
apt-get install python-virtualenv python3-pip -y
apt-get install boxes -y

VINAIGRETTE_HOME="/home/vinaigrette"

cd $VINAIGRETTE_HOME
source config/config

#ln -s /root/keys config/keys
#gpg --import config/keys/$DEBSIGN_KEYID.key
#gpg --import config/keys/$DEBSIGN_KEYID.pub

mkdir gitrepos
cd gitrepos/
git clone https://github.com/yunohost/yunohost
git clone https://github.com/yunohost/yunohost-admin
git clone https://github.com/yunohost/ssowat SSOwat
git clone https://github.com/yunohost/moulinette
git clone https://github.com/yunohost/metronome
#git clone https://github.com/YunoHost/rspamd
#git clone https://git.donarmstrong.com/unscd.git

mkdir -p /var/www/repo/debian/conf/
ln -s $VINAIGRETTE_HOME/config/distributions /var/www/repo/debian/conf/distributions

cp $VINAIGRETTE_HOME/config/nginx.conf /etc/nginx/sites-enabled/repo.conf
sed -i "s/__REPO_URL__/$REPO_URL/g" /etc/nginx/sites-enabled/repo.conf
echo "127.0.0.1 $REPO_URL" >> /etc/hosts
service nginx reload
