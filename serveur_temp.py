# regularite-TER.py
# Correpond au corrigé du dernier exercice du TD3+4 (TD3-s7.py)

import http.server
import socketserver
from urllib.parse import urlparse, parse_qs, unquote
import json

import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as pltd

import sqlite3

database = "base.sqlite"

def multiplication_liste(L):
    """ Fonction qui réalise un changement d'échelle des données."""
    res=[0 for k in L]
    for k in range(len(L)):
        res[k]=L[k]*1/10
    return (res)


#
# Définition du nouveau handler
#
class RequestHandler(http.server.SimpleHTTPRequestHandler):

  # sous-répertoire racine des documents statiques
  static_dir = '/client'

  #
  # On surcharge la méthode qui traite les requêtes GET
  #
  
  def do_GET(self):

    # On récupère les étapes du chemin d'accès
    self.init_params()
    # le chemin d'accès commence par /time
    if self.path_info[0] == 'time':
      self.send_time()
   
    # on regarde par quoi commence de chemin d'accès
    # on demande la station
    if self.path_info[0] == 'regions':
        self.send_regions()
    # on demande la station
    elif self.path_info[0] == 'temperature':
        self.send_image()
    # on spécifie un intervalle d'années
    elif self.path_info[0] == 'YearSpan':
        self.send_image(1)
    # on spécifie une station à comparer
    elif self.path_info[0] == 'STComp':
        self.send_image(2)
    
    elif self.path_info[0] == 'YearComp':
        self.send_image_2_annees()
        
    # ou pas...
    else:
      self.send_static()
  #
  # On surcharge la méthode qui traite les requêtes HEAD
  #
  def do_HEAD(self):
    self.send_static()

  #
  # On envoie le document statique demandé
  #
  def send_static(self):
    # on modifie le chemin d'accès en insérant un répertoire préfixe
    self.path = self.static_dir + self.path

    # on appelle la méthode parent (do_GET ou do_HEAD)
    # à partir du verbe HTTP (GET ou HEAD)
    if (self.command=='HEAD'):
        http.server.SimpleHTTPRequestHandler.do_HEAD(self)
    else:
        http.server.SimpleHTTPRequestHandler.do_GET(self)
  #     
  # on analyse la requête pour initialiser nos paramètres
  #
  def init_params(self):
    # analyse de l'adresse
    info = urlparse(self.path)
    
    self.path_info = [unquote(v) for v in info.path.split('/')[1:]]  # info.path.split('/')[1:]
    self.params = parse_qs(info.query)   
    # récupération du corps
    length = self.headers.get('Content-Length')
    ctype = self.headers.get('Content-Type')
    if length:
      self.body = str(self.rfile.read(int(length)),'utf-8')
      if ctype == 'application/x-www-form-urlencoded' :
        self.params = parse_qs(self.body)
    else:
      self.body = ''

  #
  # On génère et on renvoie la liste des régions et leur coordonnées (version TD3)
  #
  def send_regions(self):

    conn = sqlite3.connect(database)
    c = conn.cursor()
    
    c.execute("SELECT * FROM 'stations_meteo'")
    r = c.fetchall()
    
    headers = [('Content-Type','application/json')];
    # il faut modifier l'écriture de la latitude et de la longitude
    # pour cela il faut détailler l'écrutire de cette liste (ou dictionnaire)
    # écrire ces chiffres en décimale
    DicoStations = []
    for (staid,staname,lat,lon,hght) in r:
        latn = float(lat[1:3]) + float(lat[4:6])/60 + float(lat[7:])/3600
        lonn = float(lon[1:4]) + float(lon[5:7])/60 + float(lon[8:])/3600
        if lon[0] == '-':
            lonn *= -1
        DicoStations.append({'s':staid, 'nom':staname, 'lat': latn, 'lon':lonn ,'hght':hght})
    body = json.dumps(DicoStations)
    self.send(body,headers)

  #
  # On génère et on renvoie un graphique pour la température sur tous les relevés
  #
  def send_image(self, mode = 0):
    
    """Fonction qui renvoie un graphique d'évolution des températures
    d'une station météo selon plusieurs modes.
    0 - Affiche toute les données propres à une station
    1 - Affiche les données entre deux années
    2- Compare deux stations entre deux années"""
    
    # configuration du tracé, ne change pas avec la query
    plt.rcParams.update({'font.size': 22})
    fig1 = plt.figure(figsize=(18,6))
    ax = fig1.add_subplot(111)
    ax.set_ylim(bottom=-5,top=35)
    ax.grid(which='major', color='#888888', linestyle='-')
    ax.grid(which='minor',axis='x', color='#888888', linestyle=':')
    ax.xaxis.set_major_locator(pltd.YearLocator())
    ax.xaxis.set_minor_locator(pltd.MonthLocator())
    ax.xaxis.set_major_formatter(pltd.DateFormatter('%Y'))
    ax.xaxis.set_tick_params(labelsize=5)
    ax.xaxis.set_label_text("Date")
    ax.yaxis.set_label_text("Temperature (en degré)")
    
    conn = sqlite3.connect(database)
    c = conn.cursor()

    #Disjonction de cas selon le mode (plutôt que d'écrire 3 fonctions différents)
    # cette fonction est appelée ligne 50 par là... (03/01/2019)
    if mode == 0:
        if len(self.path_info) <= 1 or self.path_info[1] == '' : # pas de paramètre => liste par défaut
            # Definition des régions et des couleurs de tracé
            STAID = '37' #Ne sert à rien
        else:
            # On teste que la station demandée existe bien
            c.execute("SELECT DISTINCT STAID FROM 'TG_1978-2018'")
            reg = c.fetchall()
            if (self.path_info[1],) in reg:   # Rq: reg est une liste de tuples
              STAID = self.path_info[1]
            else:
                print ('Erreur nom')
                self.send_error(404)    # Région non trouvée -> erreur 404
                return None
            
        c.execute("SELECT * FROM 'TG_1978-2018' WHERE STAID=?",(STAID,))  # STAID[0][0]
        r = c.fetchall()
        # On récupères les données
    else:
        STAID = self.params['STAID'][0]
        debut = int(self.params['debut'][0])
        fin = int(self.params['fin'][0])
        #pas = int(self.params['pas'][0])
        if mode == 2:
            ST2 = self.params['ST2'][0]
        
        c.execute("SELECT * FROM 'TG_1978-2018' WHERE STAID=?",(STAID,))
        r = c.fetchall()
        R = []
        # On ne garde que les éléments qui sont les bonnes années
        # On peut le faire directement dans la requête SQL mais flemme et c'est plus safe
        for elem in r:
            year = int(elem[2][0:4])
            #print(year,debut,fin)
            if year >= debut and year <= fin:
                R.append(elem)
        r = R
        
    # On plot la première station
    x = [pltd.date2num(dt.date(int(a[2][0:4]),int(a[2][4:6]),int(a[2][6:]))) for a in r]
    # récupération de la régularité (colonne 8)
    y = [float(a[3]) for a in r]
    #Dilatation ou rétraction...
    y_fin = multiplication_liste(y)
    # tracé de la courbe
    plt.plot(x,y_fin,linewidth=0.2, linestyle='-', marker='o', color="blue", label="Temperature St n°"+str(STAID))
            
    if mode == 2:
        #print("PARAMS: ",self.params['ST2'])
        c.execute("SELECT * FROM 'TG_1978-2018' WHERE STAID=?",(ST2,))
        r = c.fetchall()
        R = []
        # On ne garde que les éléments qui sont les bonnes années
        # On peut le faire directement dans la requête SQL mais flemme
        for elem in r:
            year = int(elem[2][0:4])
            #print(year,debut,fin)
            if year >= debut and year <= fin:
                R.append(elem)
        x = [pltd.date2num(dt.date(int(a[2][0:4]),int(a[2][4:6]),int(a[2][6:]))) for a in R]
        # récupération de la régularité (colonne 8)
        y = [float(a[3]) for a in R]
        #Dilatation ou rétraction...
        y_fin = multiplication_liste(y)
        # tracé de la courbe pour la deuxième station
        plt.plot(x,y_fin,linewidth=0.2, linestyle='-', marker='x', color="red", label="Temperature St n°" + ST2)
            
    # légendes
    plt.legend(loc='lower left')
    plt.title('Températures au cours du temps',fontsize=16) 

    # génération des courbes dans un fichier PNG
    fichier = 'courbes/temperature_'+str(STAID) +'.png'
    #fichier = 'courbes/temperature.png'
    plt.savefig('client/{}'.format(fichier))
    plt.close()
    
    #Génération de l'html qui va afficher l'image à part
    """html='<!DOCTYPE html><title>Temperature</title>' +\
    '<meta charset="utf-8">' +\
    '<img src="/{}?{}" alt="temperature {}" width="100%">'.format(fichier,self.date_time_string(),self.path)"""
    body = json.dumps({
            'title': 'Température pour la station n° '+STAID, \
            'img': '/'+fichier \
             });
    # on envoie
    headers = [('Content-Type','application/json')];
    #if mode == 0:
    self.send(body,headers)
    #else:
        #self.send(html)

  def send_image_2_annees(self):
    """ fonction qui superpose les temperatures d'un station sur deux années"""
      
      
    plt.rcParams.update({'font.size': 22})
    fig1 = plt.figure(figsize=(18,6))
    ax = fig1.add_subplot(111)
    ax.set_ylim(bottom=-5,top=35)
    ax.grid(which='major', color='#888888', linestyle='-')
    ax.grid(which='minor',axis='x', color='#888888', linestyle=':')
    ax.xaxis.set_major_locator(pltd.YearLocator())
    ax.xaxis.set_minor_locator(pltd.MonthLocator())
    ax.xaxis.set_major_formatter(pltd.DateFormatter('%Y'))
    ax.xaxis.set_tick_params(labelsize=5)
    ax.xaxis.set_label_text("Date")
    ax.yaxis.set_label_text("Temperature (en degré)")
    
    conn = sqlite3.connect(database)
    c = conn.cursor()
    
    STAID = self.params['STAID'][0]
    annee1 = int(self.params['annee1'][0])
    annee2 = int(self.params['annee2'][0])
    #pas = int(self.params['pas'][0])
    
    c.execute("SELECT * FROM 'TG_1978-2018' WHERE STAID=?",(STAID,))
    r = c.fetchall()
    R1 = []
    R2 = []
    # On ne garde que les éléments qui sont les bonnes années
    # On peut le faire directement dans la requête SQL mais flemme et c'est plus safe
    for elem in r:
        year = int(elem[2][0:4])
        #print(year,debut,fin)
        if year == annee1:
            R1.append(elem)
        elif year == annee2:
            R2.append(elem)
    
    # On plot la première station
    x1 = [pltd.date2num(dt.date(annee1,int(a[2][4:6]),int(a[2][6:]))) for a in R1]
    # récupération de la régularité (colonne 8)
    y1 = [float(a[3]) for a in R1]
    #Dilatation ou rétraction...
    y1 = multiplication_liste(y1)
    # tracé de la courbe
    plt.plot(x1,y1,linewidth=0.2, linestyle='-', marker='o', color="blue", label="Temperature en "+str(annee1))
    
    # On plot la première station
    x2 = [pltd.date2num(dt.date(annee1,int(a[2][4:6]),int(a[2][6:]))) for a in R2]
    # récupération de la régularité (colonne 8)
    y2 = [float(a[3]) for a in R2]
    #Dilatation ou rétraction...
    y2 = multiplication_liste(y2)
    # tracé de la courbe
    plt.plot(x2,y2,linewidth=0.2, linestyle='-', marker='x', color="red", label="Temperature en "+str(annee2))
    
    
    # légendes
    plt.legend(loc='lower left')
    plt.title('Températures entre deux années',fontsize=16) 

    # génération des courbes dans un fichier PNG
    fichier = 'courbes/temperature_'+str(STAID) +'.png'
    #fichier = 'courbes/temperature.png'
    plt.savefig('client/{}'.format(fichier))
    plt.close()
    
    #Génération de l'html qui va afficher l'image à part
    """html='<!DOCTYPE html><title>Temperature</title>' +\
    '<meta charset="utf-8">' +\
    '<img src="/{}?{}" alt="temperature {}" width="100%">'.format(fichier,self.date_time_string(),self.path)"""
    body = json.dumps({
            'title': 'Température pour la station n° '+STAID, \
            'img': '/'+fichier \
             });
    # on envoie
    headers = [('Content-Type','application/json')];
    #if mode == 0:
    self.send(body,headers)

  #
  # On envoie les entêtes et le corps fourni
  #
  def send(self,body,headers=[]):

    # on encode la chaine de caractères à envoyer
    encoded = bytes(body, 'UTF-8')

    # on envoie la ligne de statut
    self.send_response(200)

    # on envoie les lignes d'entête et la ligne vide
    [self.send_header(*t) for t in headers]
    self.send_header('Content-Length',int(len(encoded)))
    self.end_headers()

    # on envoie le corps de la réponse
    self.wfile.write(encoded)

 
#
# Instanciation et lancement du serveur
#
httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()

