from dataclasses import dataclass

from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.addresses import Address
from pants.engine.fs import Digest
from pants.engine.internals.selectors import Get, MultiGet
from pants.engine.process import ProcessResult
from pants.engine.rules import Rule, collect_rules, rule

from pants_cargo_porcelain.subsystems import RustSubsystem, RustupTool
from pants_cargo_porcelain.target_types import CargoPackageSourcesField
from pants_cargo_porcelain.util_rules.cargo import CargoProcessRequest
from pants_cargo_porcelain.util_rules.rustup import RustToolchain, RustToolchainRequest


@dataclass(frozen=True)
class CargoBinary:
    digest: Digest


@dataclass(frozen=True)
class CargoBinaryRequest:
    address: Address
    sources: CargoPackageSourcesField
    binary_name: str

    release_mode: bool = False


@rule
async def build_cargo_binary(
    req: CargoBinaryRequest,
    rust: RustSubsystem,
    rustup: RustupTool,
) -> CargoBinary:
    source_files, toolchain = await MultiGet(
        Get(
            SourceFiles,
            SourceFilesRequest([req.sources]),
        ),
        Get(
            RustToolchain,
            RustToolchainRequest(
                "1.72.1", "x86_64-unknown-linux-gnu", ("rustfmt", "cargo", "clippy")
            ),
        ),
    )

    process_result = await Get(
        ProcessResult,
        CargoProcessRequest(
            toolchain,
            (
                "build",
                "-vv",
                f"--bin={req.binary_name}",
            ),
            source_files.snapshot.digest,
            output_files=(f"target/debug/{req.binary_name}",),
            working_directory=f"{req.address.spec_path}",
        ),
    )

    return CargoBinary(process_result.output_digest)


def rules():
    return collect_rules()
