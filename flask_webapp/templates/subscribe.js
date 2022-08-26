document.write(`<div >
        <div class="content-section" style="max-width: 30rem; margin: 1rem; float: right;  ">
                <a class="border-bottom" style="font-size: 20px"><strong ">Keep in touch – subscribe to our mailing list </strong></a>
        <div style="max-width: 100%">
        <small class="text-muted">
            Keep up to date with new dashboard features and VEPC research.  Unsubscribe at any time.</small>


        <form method="POST" action="">
        <br>
            {{ form.hidden_tag() }}
            <div style=" display: block">
            <fieldset class="form-group">
                <div class="form-group">
                    <strong>{{ form.first_name.label(class="form-control-label") }}</strong>
                    {% if form.first_name.errors %}
                        {{ form.first_name(class="form-control form-control-lg is-invalid") }}
                        <div class="invalid-feedback">
                            {% for error in form.first_name.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% else %}
                        {{ form.first_name(class="form-control form-control-lg") }}
                    {% endif %}
                </div>

                <div class="form-group">
                    <strong> {{ form.email.label(class="form-control-label") }}</strong>
                    {% if form.email.errors %}
                        {{ form.email(class="form-control form-control-lg is-invalid") }}
                        <div class="invalid-feedback">
                            {% for error in form.email.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% else %}
                        {{ form.email(class="form-control form-control-lg") }}
                    {% endif %}
                </div>
                <div style="margin-left: auto;margin-right: auto">
                    {{ form.recaptcha }}
                </div>
            </div>
                </div>


            </fieldset>
            <div class="form-group" style=" display: block">
                {{ form.submit(class="btn btn-outline-info") }}
            </div>
        </form>
    </div>
    </div>
`);