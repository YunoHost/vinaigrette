
apt-get install nginx pbuilder reprepro rebuildd gawk -y

cd /home/vinaigrette/
source config
gpg --import keys/$DEBSIGN_KEYID.key
gpg --import keys/$DEBSIGN_KEYID.pub

cd repos/
git clone https://github.com/yunohost/yunohost
git clone https://github.com/yunohost/yunohost-admin
git clone https://github.com/yunohost/ssowat
git clone https://github.com/yunohost/moulinette

mkdir -p /var/www/repo/debian/conf/

cd /home/vinaigrette/
cp distributions /var/www/repo/debian/conf/

cp /home/vinaigrette/rebuildd/rebuildd.conf /etc/rebuildd/rebuilddrc

cat keys/$DEBSIGN_KEYID.pub | apt-key add
cat /home/vinaigrette/sources.list >> /etc/apt/sources.list

ln -s /home/vinaigrette/pbuilder/images /var/cache/pbuilder/images
ln -s /var/cache/pbuilder/result /home/vinaigrette/pbuilder/result


echo "127.0.0.1 $REPO_URL" >> /etc/hosts
cp /home/vinaigrette/nginx/repo.conf /etc/nginx/sites-enabled/repo.conf
service nginx reload

rebuildd init
