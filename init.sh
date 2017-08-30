
apt-get install nginx pbuilder reprepro rebuildd gawk -y

VINAIGRETTE_HOME="/home/vinaigrette"

cd $VINAIGRETTE_HOME
source config/config

gpg --import config/keys/$DEBSIGN_KEYID.key
gpg --import config/keys/$DEBSIGN_KEYID.pub

cd gitrepos/
git clone https://github.com/yunohost/yunohost
git clone https://github.com/yunohost/yunohost-admin
git clone https://github.com/yunohost/ssowat
git clone https://github.com/yunohost/moulinette

mkdir -p /var/www/repo/debian/conf/

cd $VINAIGRETTE_HOME/
cp config/distributions /var/www/repo/debian/conf/

cp $VINAIGRETTE_HOME/rebuildd/rebuildd.conf /etc/rebuildd/rebuilddrc

cat $VINAIGRETTE_HOME/config/keys/$DEBSIGN_KEYID.pub | apt-key add
cat $VINAIGRETTE_HOME/config/sources.list >> /etc/apt/sources.list

ln -s $VINAIGRETTE_HOME/pbuilder/images /var/cache/pbuilder/images
ln -s /var/cache/pbuilder/result $VINAIGRETTE_HOME/pbuilder/result


echo "127.0.0.1 $REPO_URL" >> /etc/hosts
cp $VINAIGRETTE_HOME/conf/nginx.conf /etc/nginx/sites-enabled/repo.conf
service nginx reload

rebuildd init
