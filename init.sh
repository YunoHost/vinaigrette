
apt-get install nginx pbuilder reprepro rebuildd gawk sendxmpp -y

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

cd yunohost
git symbolic-ref refs/heads/jessie-stable refs/heads/stable
git symbolic-ref refs/heads/jessie-testing refs/heads/testing
git symbolic-ref refs/heads/jessie-unstable refs/heads/unstable
git symbolic-ref refs/heads/stretch-unstable refs/heads/stretch
cd ..

mkdir -p /var/www/repo/debian/conf/
ln -s $VINAIGRETTE_HOME/config/distributions /var/www/repo/debian/conf/distributions

rm /etc/rebuildd/rebuilddrc
ln -s $VINAIGRETTE_HOME/config/rebuildd.conf /etc/rebuildd/rebuilddrc

ln -s $VINAIGRETTE_HOME/images /var/cache/pbuilder/images
ln -s /var/cache/pbuilder/result $PBUILDER_RESULTS
cp $VINAIGRETTE_HOME/config/nginx.conf /etc/nginx/sites-enabled/repo.conf

cat $VINAIGRETTE_HOME/config/keys/$DEBSIGN_KEYID.pub | apt-key add
cat $VINAIGRETTE_HOME/config/sources.list > /etc/apt/sources.list.d/vinaigrette.list

sed -i "s/__REPO_URL__/$REPO_URL/g" /etc/nginx/sites-enabled/repo.conf
sed -i "s/__REPO_URL__/$REPO_URL/g" /etc/apt/sources.list.d/vinaigrette.list

echo "127.0.0.1 $REPO_URL" >> /etc/hosts
service nginx reload

rebuildd init
