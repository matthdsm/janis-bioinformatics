from janis_core import Boolean

from janis_bioinformatics.data_types import FastaWithDict, BamBai, BedTabix
from janis_bioinformatics.tools import BioinformaticsWorkflow
from janis_bioinformatics.tools.bcftools import BcfToolsView_1_5
from janis_bioinformatics.tools.common import SplitMultiAllele
from janis_bioinformatics.tools.illumina import Manta_1_5_0, StrelkaSomatic_2_9_10


class IlluminaSomaticVariantCaller(BioinformaticsWorkflow):
    def id(self):
        return "strelkaSomaticVariantCaller"

    def friendly_name(self):
        return "Strelka Somatic Variant Caller"

    def tool_provider(self):
        return "Variant Callers"

    def version(self):
        return "v0.1.0"

    def constructor(self):

        self.input("normal_bam", BamBai)
        self.input("tumor_bam", BamBai)

        self.input("reference", FastaWithDict)
        self.input("intervals", BedTabix(optional=True))

        self.input("is_exome", Boolean(optional=True))

        self.step(
            "manta",
            Manta_1_5_0(
                bam=self.normal_bam,
                tumorBam=self.tumor_bam,
                reference=self.reference,
                callRegions=self.intervals,
                exome=self.is_exome,
            ),
        )
        self.step(
            "strelka",
            StrelkaSomatic_2_9_10(
                indelCandidates=self.manta.candidateSmallIndels,
                normalBam=self.normal_bam,
                tumorBam=self.tumor_bam,
                reference=self.reference,
                callRegions=self.intervals,
                exome=self.is_exome,
            ),
        )
        self.step(
            "bcf_view", BcfToolsView_1_5(file=self.strelka.snvs, applyFilters=["PASS"])
        )
        self.step(
            "split_multi_allele",
            SplitMultiAllele(vcf=self.bcf_view.out, reference=self.reference),
        )

        self.output("diploid", source=self.manta.diploidSV)
        self.output("variants", source=self.strelka.snvs)
        self.output("out", source=self.split_multi_allele.out)


if __name__ == "__main__":

    wf = IlluminaSomaticVariantCaller()
    wdl = wf.translate("wdl", to_console=True, to_disk=False, write_inputs_file=False)
