Le but de l'expérimentation était de voir si je pouvais rendre cela souple. Je voulais prendre une regex par type d'info/installation par log.... L'idée était d'avoir dans une configuration le type de package manager, les types d'installation présentent dans le log et la regex par type d'installation pour extraire les Install et les Remove...


si ca marche pas comme je veux avec les regex,  je pensais reprendre un parser que j'avais déjà et l'adapter, 


Le bout le plus difficile reste de matcher les install-remove...
quand on a un bloc d'installation sans command line, on sait quels packages ont été spécifiquement demandé, car ce sont ceux qui ne sont pas automatic... mais pour les remove, ce n'est pas indiqué. On doit donc, pour chaque package, chercher dans la liste des installations plus vielles si on retrouve ce package dans une installation précédantes. Si oui, on les link. Si on demande la liste pour une date apres l'installation, mais avant le delete, on inclus le package dans la liste, mais si on demande la liste avec une date apres le delete, on ne le sort pas (sauf si il a été réinstaller).  Si on ne trouve rien, c'est que c'est un remove sans installation dans les logs et on peut l'ignorer. 

à l'interne, je pensais avoir un dictionnary avec le nom de package comme clef, et 1 liste de dataclass (install date,remove date)


Quand on interprete une entrée dans le log, il faut aussi regarder s'il y a un requested by dans les blocks qui ont un commandline. Si il n'y en a pas, c'est que c'est une installation par la distro. On ne veut pas ces packages dans notre liste...
Ex :
```Start-Date: 2023-10-06  14:26:06
Commandline: apt-get install -y --no-install-recommends gnupg software-properties-common
Install: python3-blinker:amd64 (1.4+dfsg1-0.4, automatic), libpolkit-agent-1-0:amd64 (0.105-33, automatic), libnghttp2-14:amd64 [...]
End-Date: 2023-10-06  14:26:18```

quand tu gardes tout, n'oublie pas que tu peux avoir Install:, Upgrade: et Remove: dans le meme bloc. Dans ce cas-ci, c'est facile, car on ignore les upgrade, et on a un commandline avec les packages gentilment offert sur un plateau d'argent...
```Start-Date: 2023-10-06  14:44:15
Commandline: apt-get install -y systemd pop-desktop
Install: openvpn:amd64 (2.5.5-1ubuntu3.1, automatic),[...]
Upgrade: libpam-systemd:amd64 (249.11-0ubuntu3, [...]
End-Date: 2023-10-06  14:52:36```

Il y a aussi des bloc qui n'ont pas de commandline, quand c'est installer à partir d'outils qui parlent directement avec les librairies de dpkgs. Dans ce cas, les packages installé sont ceux qui ne sont pas automatic. On ne garde pas les automatic...
```Start-Date: 2023-12-11  03:24:20
Requested-By: mbeware (1000)
Install: virt-viewer:amd64 (7.0-2build2)
End-Date: 2023-12-11  03:24:21```

voici un avec un commandline apt-get, mais pour un fichier .deb. Dans ce cas, meme si on a un commandline apt-get, le nom du package est en fait dans la ligne Install:
```Start-Date: 2023-12-11  08:42:33
Commandline: apt-get -q=2 -o Dpkg::Progress-Fancy=1 -y install /var/cache/deb-get/deb-get_0.4.0-1_all.deb
Requested-By: mbeware (1000)
Install: deb-get:amd64 (0.4.0-1)
End-Date: 2023-12-11  08:42:34```


On rencontre pas mal tout les cas avec les fichiers history.log et history.log.2 dans le retertoire Teslogs/apt sur le github du projet.


En passant, il y a des dpkgs install qui ont le nom du package... mais comme il est aussi sur la ligne Install:, je vais faire comme lorsque c'est un fichier local, et le prendre à cet endroit...
```Start-Date: 2023-12-11  09:22:37
Commandline: apt-get -q=2 -o Dpkg::Progress-Fancy=1 -y install google-chrome-stable
Requested-By: mbeware (1000)
Install: google-chrome-stable:amd64 (120.0.6099.71-1)
End-Date: 2023-12-11  09:22:46```


evidement, la partie interessante de la ligne Install: et Remove: c'est la parti <action>  <package> et [automatic] 
```Install: google-chrome-stable:amd64 (120.0.6099.71-1)
<action>: {<package>:<architecture> (<version>[,automatic])[,]}```

On pourrait être tenté de plutot prendre le fichier dpkg.log car il est plus facile à manipuler, mais il n'y a pas de moyen de savoir si c'est une installation par l'utilisateur ou si c'est un package dépendant...




