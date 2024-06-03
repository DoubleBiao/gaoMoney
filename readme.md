# Download options data from dolthub
# dolthub is a hub for dolt database system(maybe?). It is **free**!

## dolt overview:
dolt is database system that wraps mysql. dolthub is a website similar to github. It has some database maintained by dolt. To access the data, this is procedures:

download the docker file from the dolthub website:

https://www.dolthub.com/repositories/xiaotian/options/deploy?refName=master

launch the database server:

    docker buildx build -t xiaotian-options-sql-server -f xiaotian-options.dockerfile . && docker run -p 6481:6481 xiaotian-options-sql-server:latest


open another terminal and connect to the server:

    /usr/local/mysql/bin/mysql  --host 127.0.0.1 --port 6481 -u root


It would enter a cli that the type mysql command and get data. It also directly output cvs file with shell command:

    /usr/local/mysql/bin/mysql  --host 127.0.0.1 --port 6481 -u root  -e "
    USE \`options\`
    SELECT \`date\`, \`act_symbol\`, \`strike\`, \`call_put\`, \`vol\`
    FROM \`option_chain\`
    WHERE \`act_symbol\` = 'AAPL'
    " > output.csv


## option database in dolthub:
https://www.dolthub.com/repositories/xiaotian/options/data/master


## TODO
mute screen printing on server side