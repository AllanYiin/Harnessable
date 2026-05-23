def test_package_import():
    import harnessable

    assert harnessable.HarnessKernel
    assert harnessable.HarnessProject
