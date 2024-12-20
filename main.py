from flask import Flask, render_template, request
from sympy import symbols, diff, integrate, sympify, latex, Matrix
from google.cloud import storage

def upload_to_gcs(file, bucket_name):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file)
    return f"Uploaded {file.filename} to {bucket_name}."


app = Flask(__name__)

# Funcții matematice
def adunare(a, b):
    return a + b

def scadere(a, b):
    return a - b

def inmultire(a, b):
    return a * b

def impartire(a, b):
    if b != 0:
        return a / b
    else:
        return "Împărțirea la 0 nu este permisă."

def derivare(func_str, variabila):
    variabila_sym = symbols(variabila)
    func = sympify(func_str)
    derivata = diff(func, variabila_sym)
    return latex(derivata)  # Returnăm rezultatul în format LaTeX


def integrare_normala(func_str, variabila):
    variabila_sym = symbols(variabila)
    func = sympify(func_str)
    integral = integrate(func, variabila_sym)
    return latex(integral)  # Returnăm rezultatul în format LaTeX

def integrare_definita(func_str, variabila, lim_inf, lim_sup):
    variabila_sym = symbols(variabila)
    func = sympify(func_str)
    integral = integrate(func, (variabila_sym, lim_inf, lim_sup))
    return latex(integral)  # Returnăm rezultatul în format LaTeX

class Matrice:
    def __init__(self, valori):
        self.valori = valori
        self.nr_linii = len(valori)
        self.nr_coloane = len(valori[0]) if valori else 0
    
    def __repr__(self):
        return '\n'.join(' '.join(map(str, rand)) for rand in self.valori)
    
    def __add__(self, alta):
        if self.nr_linii != alta.nr_linii or self.nr_coloane != alta.nr_coloane:
            raise ValueError("Matricele trebuie să aibă aceleași dimensiuni pentru a fi adunate.")
        rezultat = [
            [self.valori[i][j] + alta.valori[i][j] for j in range(self.nr_coloane)]
            for i in range(self.nr_linii)
        ]
        return Matrice(rezultat)
    
    def __mul__(self, alta):
        if isinstance(alta, (float, int)):
            rezultat = [
                [self.valori[i][j] * alta for j in range(self.nr_coloane)]
                for i in range(self.nr_linii)
            ]
            return Matrice(rezultat)
        elif isinstance(alta, Matrice):
            if self.nr_coloane != alta.nr_linii:
                raise ValueError("Numărul de coloane al primei matrice trebuie să fie egal cu numărul de linii al celei de-a doua matrice.")
            rezultat = [[0 for _ in range(len(alta.valori[0]))] for _ in range(len(self.valori))]
        
            # Calculăm produsul matricial
            for i in range(len(self.valori)):  # Iterăm peste liniile primei matrice
                for j in range(len(alta.valori[0])):  # Iterăm peste coloanele celei de-a doua matrice
                    for k in range(len(alta.valori)):  # Iterăm peste coloanele primei matrice și liniile celei de-a doua matrice
                        rezultat[i][j] += self.valori[i][k] * alta.valori[k][j]
            return Matrice(rezultat)
        else:
            raise TypeError("Inmultirea este suportata doar intre matrice si scalar sau matrice si matrice.")
 
    def transpusa(self):
        rezultat = [
            [self.valori[j][i] for j in range(self.nr_linii)]
            for i in range(self.nr_coloane)
        ]
        return Matrice(rezultat)
    
    def inversa(self):
        if self.nr_linii != self.nr_coloane:
            raise TypeError("Inversa poate fi calculata doar pentru matrice patratice")
        matrice_sympy = Matrix(self.valori)

        if matrice_sympy.det() == 0:
            raise TypeError("Matricea nu este inversabila, determinantul este 0.")
        
        inversa_sympy = matrice_sympy.inv()
        inversa_valori = inversa_sympy.tolist()
        return Matrice(inversa_valori)
    
    def __pow__(self, exponent):
        if self.nr_linii != self.nr_coloane:
            raise TypeError("Ridicarea la putere este definita doar pentru matrice patratice.")
        if not isinstance(exponent, int) or exponent<0:
            raise TypeError("Exponentul trebuie sa fie un numar intreg pozitiv.")
        if exponent == 0:
            identitate = [[1 if i==j else 0 for j in range(self.nr_coloane)] for i in range(self.nr_linii)]
            return Matrice(identitate)
        rezultat = self
        for _ in range(exponent-1):
            rezultat = rezultat * self
        return rezultat
# Rute Flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/aritmetica', methods=['GET', 'POST'])
def aritmetica():
    if request.method == 'POST':
        a = float(request.form['a'])
        b = float(request.form['b'])
        operatie = request.form['operatie']
        if operatie == 'adunare':
            rezultat = adunare(a, b)
        elif operatie == 'scadere':
            rezultat = scadere(a, b)
        elif operatie == 'inmultire':
            rezultat = inmultire(a, b)
        elif operatie == 'impartire':
            rezultat = impartire(a, b)
        else:
            rezultat = "Operație necunoscută."
        return render_template('aritmetica.html', rezultat=rezultat, a=a, b=b, operatie=operatie)
    return render_template('aritmetica.html')

@app.route('/derivare', methods=['GET', 'POST'])
def derivare():
    rezultat = None
    if request.method == 'POST':
        func_str = request.form['functie']
        variabila = request.form['variabila']
        try:
            rezultat = derivare(func_str, variabila)
        except Exception as e:
            rezultat = f"Eroare: {e}"
        return render_template('derivare.html', func_str=func_str, variabila=variabila, rezultat=rezultat)
    return render_template('derivare.html')

@app.route('/integrare', methods=['GET', 'POST'])
def integrare():
    rezultat = None
    if request.method == 'POST':
        func_str = request.form['functie']
        variabila = request.form['variabila']
        try:
            if 'lim_inf' in request.form and 'lim_sup' in request.form:
                lim_inf = float(request.form['lim_inf'])
                lim_sup = float(request.form['lim_sup'])
                rezultat = integrare_definita(func_str, variabila, lim_inf, lim_sup)
            else:
                rezultat = integrare_normala(func_str, variabila)
        except Exception as e:
            rezultat = f"Eroare: {e}"
        return render_template('integrare.html', func_str=func_str, variabila=variabila, rezultat=rezultat)
    return render_template('integrare.html')

@app.route('/matrice', methods = ['GET', 'POST'])
def matrice():
    return render_template('matrice.html')

@app.route('/matrice/adunare', methods = ['GET', 'POST'])
def matrice_adunare():
    rezultat = None
    if request.method == 'POST':
        try:
            mat1 = eval(request.form ['matrice1'])
            mat2 = eval(request.form ['matrice2'])

            mat1 = Matrice(mat1)
            mat2 = Matrice(mat2)

            suma = mat1+mat2

            rezultat = suma.__repr__()
        except Exception as e:
            rezultat = f"Eroare: {e}"
    return render_template("matrice_adunare.html", rezultat = rezultat)

@app.route('/matrice/inmultire', methods = ['GET', 'POST'])
def matrice_inmultire():
    rezultat = None
    if request.method == 'POST':
        try:
            mat1 = eval(request.form['matrice1'])
            operand = request.form['operand']

            mat1 = Matrice(mat1)

            if operand.isdigit() or '.' in operand:
                scalar = float(operand)
                rezultat = mat1 * scalar
            else:
                mat2 = eval(operand)
                mat2 = Matrice(mat2)
                rezultat = mat1 * mat2
            rezultat = rezultat.__repr__()
        except Exception as e:
            rezultat = f"Eroare: {e}"
    return render_template("matrice_inmultire.html", rezultat = rezultat)

@app.route('/matrice/transpusa', methods = ['GET', 'POST'])
def matrice_transpusa():
    rezultat = None
    if request.method == 'POST':
        try:
            mat = eval(request.form['matrice'])
            mat = Matrice(mat)
            rezultat = mat.transpusa().__repr__()
        except Exception as e:
            rezultat = f"Eroare: {e}"
    return render_template("matrice_transpusa.html", rezultat = rezultat)

@app.route('/matrice/inversa', methods = ['GET', 'POST'])
def matrice_inversa():
    rezultat = None
    if request.method == 'POST':
        try:
            mat = eval(request.form['matrice'])
            mat = Matrice(mat)
            rezultat = mat.inversa().__repr__()
        except Exception as e:
            rezultat = f"Eroare: {e}"
    return render_template("matrice_inversa.html", rezultat = rezultat)

@app.route('/matrice/putere', methods = ['GET', 'POST'])
def matrice_putere():
    rezultat = None
    if request.method == 'POST':
        try:
            mat = eval(request.form['matrice'])
            exponent = int(request.form['exponent'])
            mat = Matrice(mat)
            rezultat = mat ** exponent
            rezultat = rezultat.__repr__()
        except Exception as e:
            rezultat = f"Eroare: {e}"
    return render_template ('matrice_putere.html', rezultat = rezultat)

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, world!"

if __name__ == "__main__":
    app.run(debug=True)
