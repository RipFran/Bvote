#!/bin/bash

#Colours
greenColour="\e[0;32m\033[1m"
endColour="\033[0m\e[0m"
redColour="\e[0;31m\033[1m"
blueColour="\e[0;34m\033[1m"
yellowColour="\e[0;33m\033[1m"
purpleColour="\e[0;35m\033[1m"
turquoiseColour="\e[0;36m\033[1m"
grayColour="\e[0;37m\033[1m"


trap ctrl_c INT

function ctrl_c(){
	echo -e "\n${yellowColour}[*]${endColour}${grayColour} Saliendo...\n${endColour}"
	tput cnorm; exit 1
}


function helpPanel(){
    echo -e "\n${yellowColour}[*]${endColour}${grayColour} Uso ./autoBase.sh\n${endColour}"
   for i in $(seq 1 85); do echo -ne "${redColour}-"; done; echo -ne "${endColour}"
   echo -e "\n\n\t${grayColour}[-a]${endColour}${yellowColour} Crear nuevas elecciones vacias (-a <nombre elecciones>)${endColour}"
   echo -e "\n\t${grayColour}[-A]${endColour}${yellowColour} Creacion de las elecciones con recipients aleatorios (-A <nombre elecciones>) ${endColour}"
   echo -e "\n\t${grayColour}[-d]${endColour}${yellowColour} Eliminar elecciones (-d <nombre elecciones>) ${endColour}"
   echo -e "\n\t${grayColour}[-s]${endColour}${yellowColour} Mostrar elecciones existentes${endColour}"
   echo -e "\n\t${grayColour}[-i]${endColour}${yellowColour} Inicializar base de datos (DB usuaris)${endColour}"
   echo -e "\n\t${grayColour}[-v]${endColour}${yellowColour} Crear votante${endColour}"
   echo -e "\n\t${grayColour}[-h]${endColour}${yellowColour} Mostrar este panel de ayuda${endColour}\n"

   exit 1
}

function showDBs(){
    databases=$(mysql -u alumne -palumne -e "show databases;" | grep -vE "information_schema|mysql|performance_schema|Database|usuaris")
    echo
    i=0
    for db in $databases; do
        i+=1
        echo -e "\t${purpleColour}$db${endColour}"
    done

    if [ $i -eq 0 ]; then
        echo -e "\t${redColour}No hi ha ninguna eleccio${endColour}"
    fi
    echo
}

function initDB() {
    bash -c "mariadb --version"
    var=$?
    if [[ "$var" != "0" ]]; then
        sudo apt update
        sudo apt install mariadb-server
        sudo mysql_secure_installation
    fi
    echo -e "\t${greenColour}MariaDB instaldo${endColour}"
    echo -e "\t${greenColour}Creando usuario 'alumne' con contraseña 'alumne'${endColour}"
    bash -c "sudo mariadb -u root -e \"CREATE USER 'alumne' IDENTIFIED BY 'alumne'\""
    bash -c "sudo mariadb -u root -e \"GRANT ALL PRIVILEGES ON *.* TO 'alumne';\""
    echo -e "\t${greenColour}Creando base de datos 'usuaris'${endColour}"
    mysql -u alumne -palumne -e "create database usuaris"
    mysql -u alumne -palumne usuaris < usuaris.sql
}

function createSender() {
    echo "Introduce DNI del votante"
    read dni
    echo "Introduce contraseña del votante"
    read password 
    echo "Votaciones en las que puede votar (todo junto y separadas por comas)"
    read votaciones 
    bash -c "mysql -u alumne -palumne -e \"insert into usuaris.usuaris(dni,passwd,canVote,isGenerated,hasVoted) values('$dni','$password','$votaciones','$votaciones','$votaciones')\""

}

function deleteDB() {
    bash -c "mysql -u alumne -palumne -e \"drop database $dat\" 2>/dev/null && echo -e \"\n\t${purpleColour}Base de datos ${endColour}${grayColour}$dat${endColour}${purpleColour} borrada satisfactoriamente\n${endColour}\" || echo -e \"\n\t${redColour}Base de datos ${endColour}${grayColour}$dat${endColour}${redColour} no encontrada\n${endColour}\""
    rm -rf $dat
}

function createRandomDB(){

    bash -c "mysql -u alumne -palumne -e \"create database $dat\"  2>/dev/null"
    var=$?
    if [ "$var" = "0" ]; then
        echo -e "\n\t${purpleColour}Base de datos ${endColour}${grayColour}$dat${endColour}${purpleColour} creada\n${endColour}"
        bash -c "mysql -u alumne -palumne $dat < elecciones.sql"
        mkdir $dat

        echo -e "\t${purpleColour}Creando 5 recipients${endColour}"
        sleep 1
        for i in $(seq 1 5); do
            bash -c "openssl genrsa 1024 > $dat/key$i.pem" 
            bash -c "openssl rsa -in $dat/key$i.pem -outform PEM -pubout -out $dat/public$i.pem"

            publicKey=$(bash -c "tr -d \"\n\" < $dat/public$i.pem | sed 's/KEY-----/KEY-----\\\n/' | sed 's/-----END/\\\n-----END/g'")
            
            bash -c "mysql -u alumne -palumne -e \"insert into $dat.recipientsPK(pk,entidad) values('$publicKey','$i')\""

        done
        echo -e "\t${purpleColour}Recipients creados${endColour}"
        sleep 1
        echo -e "\n\t${greenColour}Elecciones con recipients aleatorios creadas\n${endColour}"

    else 
        echo -e "\n\t${redColour}Base de datos ${endColour}${grayColour}$dat${endColour}${redColour} ya existe\n${endColour}"
    fi
}

function createDB(){
    bash -c "mysql -u alumne -palumne -e \"create database $dat\"  2>/dev/null"
    var=$?
    if [ "$var" = "0" ]; then
        bash -c "mysql -u alumne -palumne $dat < elecciones.sql"
        echo -e "\n\t${greenColour}Elecciones creadas\n${endColour}"
    else
        echo -e "\n\t${redColour}Base de datos ${endColour}${grayColour}$dat${endColour}${redColour} ya existe\n${endColour}"
    fi
}

parameter_counter=0;while getopts "a:d:A:shiv" arg; do
    case $arg in
        a) dat=$OPTARG; let parameter_counter=1;;
        d) dat=$OPTARG; let parameter_counter=2;;
        A) dat=$OPTARG; let parameter_counter=3;;
        s) let parameter_counter=4;;
        i) let parameter_counter=5;;
        v) let parameter_counter=6;;
        h) helpPanel;;
        
    esac
done

if [ $parameter_counter -eq 0 ]; then
    helpPanel
elif [ $parameter_counter -eq 1 ]; then
    createDB
elif [ $parameter_counter -eq 2 ]; then
    deleteDB
elif [ $parameter_counter -eq 3 ]; then
    createRandomDB
elif [ $parameter_counter -eq 4 ]; then
    showDBs
elif [ $parameter_counter -eq 5 ]; then
    initDB
elif [ $parameter_counter -eq 6 ]; then
    createSender
fi


