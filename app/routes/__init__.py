def register_routes(app):
    from .auth import auth
    from .dashboard import dashboard
    from .modulo1 import modulo1
    from .modulo2 import modulo2
    from .modulo3 import modulo3
    from .modulo4 import modulo4
    from .modulo5 import modulo5
    from .modulo6 import modulo6
    from .modulo7 import modulo7
    from .modulo8 import modulo8
    from .modulo9 import modulo9

    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(modulo1)
    app.register_blueprint(modulo2)
    app.register_blueprint(modulo3)
    app.register_blueprint(modulo4)
    app.register_blueprint(modulo5)
    app.register_blueprint(modulo6)
    app.register_blueprint(modulo7)
    app.register_blueprint(modulo8)
    app.register_blueprint(modulo9)
