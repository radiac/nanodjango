from django.template import Context, Template


def test_simple_tag(nanodjango_app):
    @nanodjango_app.templatetag.simple_tag
    def test_tag():
        return "hello world"

    # Use the actual app_name from the Django instance
    template = Template("{% load " + nanodjango_app.app_name + " %}{% test_tag %}")
    rendered = template.render(Context())
    assert rendered == "hello world"


def test_simple_tag_with_args(nanodjango_app):
    @nanodjango_app.templatetag.simple_tag
    def greet_tag(name, greeting="Hello"):
        return f"{greeting}, {name}!"

    template = Template(
        "{% load " + nanodjango_app.app_name + " %}{% greet_tag 'Alice' %}"
    )
    rendered = template.render(Context())
    assert rendered == "Hello, Alice!"


def test_simple_tag_with_context(nanodjango_app):
    @nanodjango_app.templatetag.simple_tag(takes_context=True)
    def context_tag(context):
        return f"user: {context.get('user', 'anonymous')}"

    template = Template("{% load " + nanodjango_app.app_name + " %}{% context_tag %}")
    rendered = template.render(Context({"user": "testuser"}))
    assert rendered == "user: testuser"


def test_simple_tag_with_custom_name(nanodjango_app):
    @nanodjango_app.templatetag.simple_tag(name="custom_name")
    def some_function():
        return "custom output"

    template = Template("{% load " + nanodjango_app.app_name + " %}{% custom_name %}")
    rendered = template.render(Context())
    assert rendered == "custom output"


def test_filter(nanodjango_app):
    @nanodjango_app.templatetag.filter
    def upper_filter(value):
        return value.upper()

    template = Template(
        "{% load " + nanodjango_app.app_name + " %}{{ 'hello'|upper_filter }}"
    )
    rendered = template.render(Context())
    assert rendered == "HELLO"


def test_filter_with_custom_name(nanodjango_app):
    @nanodjango_app.templatetag.filter(name="shout")
    def loud_filter(value):
        return f"{value}!"

    template = Template("{% load " + nanodjango_app.app_name + " %}{{ 'test'|shout }}")
    rendered = template.render(Context())
    assert rendered == "test!"


def test_inclusion_tag(nanodjango_app):
    # Create a simple template string for the inclusion tag
    nanodjango_app.templates = {"test_include.html": "Name: {{ name }}"}

    @nanodjango_app.templatetag.inclusion_tag("test_include.html")
    def show_name(name):
        return {"name": name}

    template = Template(
        "{% load " + nanodjango_app.app_name + " %}{% show_name 'Bob' %}"
    )
    rendered = template.render(Context())
    assert "Name: Bob" in rendered


def test_custom_tag(nanodjango_app):
    from django.template import Node

    class CustomNode(Node):
        def render(self, context):
            return "custom node output"

    @nanodjango_app.templatetag.tag
    def custom_tag(parser, token):
        return CustomNode()

    template = Template("{% load " + nanodjango_app.app_name + " %}{% custom_tag %}")
    rendered = template.render(Context())
    assert rendered == "custom node output"


def test_custom_tag_with_name(nanodjango_app):
    from django.template import Node

    class NamedCustomNode(Node):
        def render(self, context):
            return "named custom node output"

    @nanodjango_app.templatetag.tag("named_custom")
    def some_function(parser, token):
        return NamedCustomNode()

    template = Template("{% load " + nanodjango_app.app_name + " %}{% named_custom %}")
    rendered = template.render(Context())
    assert rendered == "named custom node output"


def test_simple_block_tag(nanodjango_app):
    @nanodjango_app.templatetag.simple_block_tag
    def upper_block(content):
        return content.upper()

    template = Template(
        "{% load "
        + nanodjango_app.app_name
        + " %}{% upper_block %}hello world{% endupper_block %}"
    )
    rendered = template.render(Context())
    assert rendered == "HELLO WORLD"


def test_simple_block_tag_with_args(nanodjango_app):
    @nanodjango_app.templatetag.simple_block_tag
    def repeat_block(content, times):
        return content * int(times)

    template = Template(
        "{% load "
        + nanodjango_app.app_name
        + " %}{% repeat_block 3 %}Hi! {% endrepeat_block %}"
    )
    rendered = template.render(Context())
    assert rendered == "Hi! Hi! Hi! "


def test_simple_block_tag_with_context(nanodjango_app):
    @nanodjango_app.templatetag.simple_block_tag(takes_context=True)
    def context_block(context, content):
        user = context.get("user", "anonymous")
        return f"{user}: {content.strip()}"

    template = Template(
        "{% load "
        + nanodjango_app.app_name
        + " %}{% context_block %}Hello world{% endcontext_block %}"
    )
    rendered = template.render(Context({"user": "testuser"}))
    assert rendered == "testuser: Hello world"


def test_simple_block_tag_with_custom_name(nanodjango_app):
    @nanodjango_app.templatetag.simple_block_tag(name="shout")
    def loud_block(content):
        return f"{content.upper()}!"

    template = Template(
        "{% load " + nanodjango_app.app_name + " %}{% shout %}hello{% endshout %}"
    )
    rendered = template.render(Context())
    assert rendered == "HELLO!"


def test_simple_block_tag_with_kwargs(nanodjango_app):
    @nanodjango_app.templatetag.simple_block_tag
    def format_block(content, prefix="", suffix="", upper=False):
        result = content.strip()
        if upper:
            result = result.upper()
        return f"{prefix}{result}{suffix}"

    template = Template(
        "{% load "
        + nanodjango_app.app_name
        + " %}{% format_block prefix='[' suffix=']' upper=True %}hello world{% endformat_block %}"
    )
    rendered = template.render(Context())
    assert rendered == "[HELLO WORLD]"


def test_registration_tracking(nanodjango_app):
    """Test that template tags are tracked for conversion"""

    @nanodjango_app.templatetag.simple_tag(name="tracked_tag")
    def tracked():
        return "tracked"

    @nanodjango_app.templatetag.filter
    def tracked_filter(value):
        return value

    @nanodjango_app.templatetag.simple_block_tag(name="tracked_block")
    def tracked_block(content):
        return content

    # Check that tags were registered for conversion
    registered = nanodjango_app._templatetag._registered

    # Find our registered items
    tracked_items = [
        item
        for item in registered
        if item[1].__name__ in ["tracked", "tracked_filter", "tracked_block"]
    ]
    assert len(tracked_items) == 3

    # Check simple_tag registration
    simple_tag_item = next(item for item in tracked_items if item[0] == "simple_tag")
    assert simple_tag_item[2] == {"name": "tracked_tag"}

    # Check filter registration
    filter_item = next(item for item in tracked_items if item[0] == "filter")
    assert filter_item[2] == {}

    # Check simple_block_tag registration
    block_tag_item = next(
        item for item in tracked_items if item[0] == "simple_block_tag"
    )
    assert block_tag_item[2] == {"name": "tracked_block"}
