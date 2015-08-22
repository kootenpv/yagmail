""" Unused so far"""


class InlineIMG():

    def __init__(self, path):
        self.path = path
        self.is_local = False
        self.id = abs(hash(self.path))
        self.name = self.id
        self.mime_object = self.makeMIME()
        self.html_node = self.html_node()

    def __repr__(self):
        """ The representation of the image.
            It is also the fallback text for clients that cannot display HTML
        """
        if self.is_local:
            fname = mask_local_path(self.path)
        else:
            fname = self.path
        return '<img {} should be here'.format(fname)

    def decide_local_path_or_external():
        if can_load_local:
            self.is_local = True
        elif can_load_as_url:
            self.is_local = False
        else:
            raise Exception('Invalid')

    def mask_local_path():
        return ".../" + self.path.split('/')[-1]

    def html_node(self):
        return '<img src="cid:{}" title="{}"/>'.format(self.id, self.name)

    def makeMIME(self):
        mime_object.add_header('Content-ID', '<{}>'.format(self.id))
        email.encoders.encode_base64(content_object['mime_object'])
