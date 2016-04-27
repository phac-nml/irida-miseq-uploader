import wx
import logging
import threading
from wx.lib.pubsub import pub
from API.qualitycontrol import fastq_stats

class OrganismChoice:
    def __init__(self, organism_name, organism_genome_length):
        self._organism_name = organism_name
        self._organism_genome_length = organism_genome_length

    @property
    def organism_name(self):
        return self._organism_name

    @property
    def organism_genome_length(self):
        return self._organism_genome_length

class SamplePanel(wx.Panel):
    organism_choices = {OrganismChoice("Listeria", 3000000),
                         OrganismChoice("E. coli/Shigella", 5000000),
                         OrganismChoice("Salmonella", 5000000),
                         OrganismChoice("Campylobacter", 1600000)}

    def __init__(self, parent, sample):
        wx.Panel.__init__(self, parent)
        self._sample = sample
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._checkbox = wx.CheckBox(self, label=self._sample.get_id(), style=wx.CHK_3STATE|wx.CHK_ALLOW_3RD_STATE_FOR_USER)
        self._organism = wx.ComboBox(self)

        for organism in SamplePanel.organism_choices:
            self._organism.Append(organism.organism_name, organism)

        self.sizer.Add(self._checkbox, proportion=2)
        self.sizer.Add(self._organism, proportion=2)

        self.sizer.Add(wx.StaticText(self, label="298 / 399MB"))
        self._gauge = wx.Gauge(self, range=100)
        self._gauge.SetValue(75)
        self.sizer.Add(self._gauge)
        self.SetSizer(self.sizer)
        self.Layout()

        pub.subscribe(self._add_qc_data, "quality_control_results-" + sample.get_id())
        threading.Thread(target=fastq_stats, kwargs={"filename": sample.get_files()[0], "event_name": "quality_control_results-" + sample.get_id()}).start()

    def _add_qc_data(self, fastq_stats):
        logging.info("QC finished, adding sample results")
        self.Freeze()
        self.sizer.Add(wx.StaticText(self, label=str(fastq_stats)))
        self.Layout()
        self.Thaw()
