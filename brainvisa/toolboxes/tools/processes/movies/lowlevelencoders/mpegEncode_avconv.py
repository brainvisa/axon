from brainvisa.processes import *
from brainvisa.validation import ValidationError
from brainvisa.configuration import mpegConfig

name = 'avconv MPEG encoder'
userLevel = 2


def validation():
    if 'avconv' not in mpegConfig.encoders:
        raise ValidationError(_t_('avconv not present'))


def codecs():
    c = mpegConfig.codecs.get('avconv')
    if c is not None:
        return c
    return {}


signature = Signature(
    'images', ListOf(ReadDiskItem('2D Image', 'aims Image Formats',
                                  ignoreAttributes=1)),
    'animation', WriteDiskItem('MPEG film', mpegConfig.mpegFormats),
    'encoding', Choice(*codecs()),
    'quality', Integer(),
    'framesPerSecond', Integer(),
    'passes', Choice(1, 2),
    'additional_encoder_options', ListOf(String()),
)


def initialization(self):
    self.quality = 75
    self.framesPerSecond = 25
    self.passes = 1
    for c in ('h264', 'mpeg4', 'msmpeg4'):
        if c in codecs():
            self.encoding = c
            break
    if self.encoding is None and len(codecs()) >= 0:
        self.encoding = codecs()[0]


def execution(self, context):
    context.runProcess(
        'mpegEncode_ffmpeg', images=self.images, animation=self.animation,
        encoding=self.encoding, quality=self.quality,
        framesPerSecond=self.framesPerSecond, passes=self.passes,
        additional_encoder_options=self.additional_encoder_options)
